import atexit
import importlib
import inspect
import logging
import os.path
import pickle
import sys
from argparse import ArgumentParser
from datetime import timedelta
from enum import StrEnum
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional, Tuple, Callable, Any, Dict, Type, Union

import flask
from flask import Flask, request, abort, Response
from flask_cors import CORS

from raspberry_py.gpio import Component, setup, cleanup

# keyboard keys
LEFT_ARROW_KEYS = ['Left', 'ArrowLeft']
RIGHT_ARROW_KEYS = ['Right', 'ArrowRight']
UP_ARROW_KEYS = ['Up', 'ArrowUp']
DOWN_ARROW_KEYS = ['Down', 'ArrowDown']
SPACE_KEY = [' ']

# mapping from (a) type name specified in the REST GET query to (b) python function that converts the value to a python
# object.
CALL_TYPE_CAST_FUNCTIONS = {
    int.__name__: int,
    str.__name__: str,
    float.__name__: float,
    bool.__name__: lambda s: s.lower() == 'true',
    'days': lambda days: timedelta(days=float(days)),
    'hours': lambda hours: timedelta(hours=float(hours)),
    'minutes': lambda minutes: timedelta(minutes=float(minutes)),
    'seconds': lambda seconds: timedelta(seconds=float(seconds)),
    'milliseconds': lambda milliseconds: timedelta(milliseconds=float(milliseconds))
}

# the smallest possible blank jpeg, encoded as base-64 string.
BLANK_JPEG_BASE_64_STR = (
    '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC'
    '4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA'
    'AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0'
    'KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm'
    'p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8'
    'QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK'
    'U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6O'
    'nq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=='
)


class CallImageBytes(str):
    """
    Special return type for RpyFlask calls that want to display an image/icon in the call history. This must be a
    base-64 encoded string of the image bytes, to be used as the source (src) of an HTML image.
    """


class Call:
    """
    Record of a call.
    """

    def __init__(
            self,
            component_id: str,
            function_name: str,
            arg_value: Dict
    ):
        """
        Initialize the call.

        :param component_id: Component id.
        :param function_name: Function name.
        :param arg_value: Argument values.
        """

        self.component_id = component_id
        self.function_name = function_name
        self.arg_value = arg_value

        self.call_image_bytes: CallImageBytes = CallImageBytes(BLANK_JPEG_BASE_64_STR)

    def __eq__(
            self,
            other
    ) -> bool:
        """
        Check equality with an object.

        :param other: Other object.
        :return: True if equal and False otherwise.
        """

        if not isinstance(other, Call):
            raise ValueError(f'Expected a {Call}')

        return (
            self.component_id == other.component_id and
            self.function_name == other.function_name and
            self.arg_value == other.arg_value
        )

    def __ne__(
            self,
            other
    ) -> bool:
        """
        Check inequality with an object.

        :param other: Other object.
        :return: True if not equal and False otherwise.
        """

        return not self.__eq__(other)

    def __str__(
            self
    ) -> str:
        """
        Get string.

        :return: String.
        """

        return f'{self.component_id}/{self.function_name}:  {self.arg_value}'

    def execute(
            self
    ) -> Tuple[Response, Any]:
        """
        Execute the call.

        :return: 2-tuple of the Flask Response and the call function's raw (verbatim) return value.
        """

        component = app.id_component[self.component_id]

        if hasattr(component, self.function_name):

            function = getattr(component, self.function_name)
            function_return_value = function(**self.arg_value)

            # if the function returned call-image bytes, then set them on the current Call object. there is no return
            # value from the REST call in this case, since the image bytes are intended to be consumed here and not
            # returned to the caller. only set the image the first time.
            if isinstance(function_return_value, CallImageBytes) and self.call_image_bytes == BLANK_JPEG_BASE_64_STR:
                self.call_image_bytes = function_return_value
                flask_response = flask.jsonify(None)
            else:
                flask_response = flask.jsonify(function_return_value)

            return flask_response, function_return_value

        else:
            abort(
                HTTPStatus.NOT_FOUND,
                f'Component {component} (id={self.component_id}) has no function named {self.function_name}.'
            )


class CallHistory(Component):
    """
    Component that records, loads, saves, and composes the call history of the RpyFlask application.
    """

    class State(Component.State):

        def __init__(
                self,
                calls: List[Call],
                macros: List[List[int]]
        ):
            """
            Initialize the state.

            :param calls: Calls.
            :param macros: Macros, each of which is a list of indices in the history to be called.
            """

            self.calls: List[Call] = calls
            self.macros: List[List[int]] = macros

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another object.

            :param other: Other object.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, CallHistory.State):
                raise ValueError(f'Expected a {CallHistory.State}')

            return self.calls == other.calls and self.macros == other.macros

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

            return f'calls:  {len(self.calls)}; macros:  {len(self.macros)}'

    def __init__(
            self
    ):
        """
        Initialize the component.
        """

        super().__init__(CallHistory.State([], []))

        self.record_macro = False
        self.macro_call_indices: List[int] = []

    def add(
            self,
            call_reference: Call
    ):
        """
        Add call reference.

        :param call_reference: Call reference.
        """

        state: CallHistory.State = self.state

        calls = state.calls.copy()
        calls.append(call_reference)

        self.set_state(CallHistory.State(calls, state.macros))

    def execute(
            self,
            item_idx: int
    ) -> Tuple[Response, Any]:
        """
        Execute a call from the history.

        :param item_idx: History item index to execute.
        :return: 2-tuple of the Flask Response and the call function's raw (verbatim) return value.
        """

        state: CallHistory.State = self.state

        return state.calls[item_idx].execute()

    def remove(
            self,
            item_idx: int
    ):
        """
        Remove a call from the history.

        :param item_idx: History item index to remove.
        """

        state: CallHistory.State = self.state
        del state.calls[item_idx]

    def list(
            self
    ) -> List[Dict]:
        """
        List calls.

        :return: Calls.
        """

        state: CallHistory.State = self.state

        return [
            {
                'image': f'{c.call_image_bytes}',
                'title': f'{c.function_name}',
                'description': f'{c.arg_value}'
            }
            for c in state.calls
        ]

    def start_macro(
            self
    ):
        """
        Start recording call executions until `save_macro` is called, at which point a macro-call will be added to the
        history.
        """

        if self.record_macro:
            logging.warning('Already recording a macro. It does not make sense to call start_macro.')
        else:
            self.record_macro = True

    def save_macro(
            self
    ):
        """
        Save the current macro.
        """

        if self.record_macro:

            state: CallHistory.State = self.state

            # add the macro
            macros = state.macros.copy()
            macro_idx = len(macros)
            macro = self.macro_call_indices.copy()
            macros.append(macro)

            # add the macro-call
            calls = state.calls.copy()
            call_idx = len(calls)
            macro_call = Call(
                self.id,
                self.run_macro.__name__,
                {
                    'macro_idx': macro_idx,
                    'call_idx': call_idx
                }
            )
            calls.append(macro_call)

            # set state and clear macro
            self.set_state(CallHistory.State(calls, macros))
            self.macro_call_indices.clear()
            self.record_macro = False
            logging.info(f'Saved new macro {macro_idx} as call {call_idx}. Calls in macro:  {macro}')

        else:
            logging.warning('Cannot save macro when not currently recording one.')

    def run_macro(
            self,
            macro_idx: int,
            call_idx: int
    ):
        """
        Run a macro.

        :param macro_idx: Macro index to run.
        :param call_idx: Index of the Call associated with the macro.
        """

        state: CallHistory.State = self.state

        # execute each call in the macro
        final_function_return_value = None
        for call_history_item_idx in state.macros[macro_idx]:
            _, final_function_return_value = self.execute(call_history_item_idx)

        # set the macro-call image to the final returned image
        macro_call = state.calls[call_idx]
        if isinstance(final_function_return_value, CallImageBytes):
            if macro_call.call_image_bytes == BLANK_JPEG_BASE_64_STR:
                macro_call.call_image_bytes = final_function_return_value
        else:
            raise ValueError(
                f'Expected the final call of the macro to return image bytes, but it returned:  '
                f'{final_function_return_value}'
            )

    def get_ui_elements(
            self
    ) -> List[Tuple[Union[str, Tuple[str, str]], str]]:
        """
        Get UI elements for the current component.

        :return: List of 2-tuples of (1) element key and (2) UI element.
        """

        list_id, list_ui_element = RpyFlask.get_action_button_list(self.id, self.list, timedelta(seconds=1.0), "200px", "200px", [(self.execute, 'Run'), (self.remove, 'Delete')])

        return [
            (list_id, list_ui_element),
            RpyFlask.get_switch(self.id, self.start_macro, self.save_macro, 'Record Macro', False)
        ]


class RpyFlask(Flask):
    """
    Extension of Flask that adds raspberry-py GPIO components.
    """

    def __init__(
            self,
            import_name: str
    ):
        """
        Initialize the RpyFlask.

        :param import_name: Import name. See Flask documentation.
        """

        super().__init__(import_name=import_name)

        self.id_component = {}
        self.root_components = []
        self.on_exit_callbacks: List[Callable[[], Any]] = []

        state_dir = expanduser('~/.raspberry-py')
        os.makedirs(state_dir, exist_ok=True)
        self.state_path = join(state_dir, 'state.json')

    def add_component(
            self,
            component: Component
    ):
        """
        Add a component to the app. This will recursively add subcomponents of the component. Any component passed here
        must implement its `get_ui_elements` function to obtain its UI elements.

        :param component: Component.
        """

        self._add_component(component, True)

    def _add_component(
            self,
            component: Component,
            root: bool
    ):
        """
        Internal function for adding a component and recursively adding its subcomponents.

        :param component: Component.
        :param root: Whether the component is a root component.
        """

        self.id_component[component.id] = component

        if root:
            self.root_components.append(component)

        for component in component.get_subcomponents():
            self._add_component(component, False)

    def save_state(
            self
    ):
        """
        Save state.
        """

        with open(self.state_path, 'wb') as f:
            history = [c for c in self.id_component.values() if isinstance(c, CallHistory)][0]
            history_state: CallHistory.State = history.state
            pickle.dump(history_state, f)
            logging.info(f'Saved call history state ({history_state}):  {self.state_path}')

    def load_state(
            self
    ):
        """
        Load state.
        """

        if os.path.exists(self.state_path):
            logging.info(f'Loading state:  {self.state_path}')
            with open(self.state_path, 'rb') as f:
                history = [c for c in self.id_component.values() if isinstance(c, CallHistory)][0]
                history_state: CallHistory.State = pickle.load(f)
                history.state = history_state
                logging.info(f'Loaded call history state ({history_state}):  {self.state_path}')
        else:
            logging.info(f'No call history state exists:  {self.state_path}')

    def on_exit(
            self
    ):
        """
        Save state and signal that the process running the app is about to exit.
        """

        self.save_state()

        for callback in self.on_exit_callbacks:
            callback()

    def register_on_exit_callback(
            self,
            callback: Callable[[], Any]
    ):
        """
        Register a callback function to be invoked when the application is exiting.

        :param callback: Function.
        """

        self.on_exit_callbacks.append(callback)


    def write_component_files(
            self,
            rest_host: str,
            rest_port: int,
            dir_path: str
    ):
        """
        Write files for raspberry-py components in the current application.

        :param rest_host: Host serving the REST application.
        :param rest_port: Port serving the REST application.
        :param dir_path: Directory in which to write files (will be created if it does not exist).
        """

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        for component in self.root_components:
            for element_id, element_content in component.get_ui_elements():

                # element id can be either a string (which is assumed to be html) or a 2-tuple of the id and extension.
                if isinstance(element_id, str):
                    file_name = f'{element_id}.html'
                elif isinstance(element_id, tuple) and len(element_id) == 2:
                    file_name = '.'.join(element_id)
                else:
                    raise ValueError(f'Invalid element id:  {element_id}')

                path = join(dir_path, file_name)
                with open(path, 'w') as component_file:
                    component_file.write(f'{element_content}\n')
                print(f'Wrote {path}')

        globals_path = join(dir_path, 'globals.js')
        with open(globals_path, 'w') as globals_file:
            globals_file.writelines([
                f'export const rest_host = "{rest_host}";\n',
                f'export const rest_port = {rest_port};'
            ])
        print(f'Wrote {globals_path}')

        utils_path = join(dir_path, 'utils.js')
        with open(utils_path, 'w') as utils_file:
            utils_file.write("""
const element_id_call_time = {};
const element_id_latency = {};
const element_id_alpha = {};

export function init_latency(element_id, alpha) {
  element_id_latency[element_id] = null;
  element_id_alpha[element_id] = alpha;
}

export function set_call_time(element_id) {
  element_id_call_time[element_id] = Date.now()
}

export function update_latency(element_id) {
    const latency = Date.now() - element_id_call_time[element_id];
    const alpha = element_id_alpha[element_id];
    let running_latency = element_id_latency[element_id];
    if (running_latency === null) {
      running_latency = latency;
    }
    else {
      running_latency = alpha * running_latency + (1.0 - alpha) * latency;
    }
    element_id_latency[element_id] = running_latency;
    return running_latency;
}

export async function is_checked(element) {
  while (!element.is(":checked")) {
    await new Promise(r => setTimeout(r, 1000));
  }
}
""")
            print(f'Wrote {utils_path}')

    @staticmethod
    def get_switch(
            component_id: str,
            on_function: Optional[Callable[[], None]],
            off_function: Optional[Callable[[], None]],
            text: Optional[str],
            initially_on: bool
    ) -> Tuple[str, str]:
        """
        Get switch UI element.

        :param component_id: Component id.
        :param on_function: Function to call when switch is switched on, or None for no scripting (value only).
        :param off_function: Function to call when switch is switched off, or None for no scripting (value only).
        :param text: Readable text to display.
        :param initially_on: Initially on.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        if on_function is None or off_function is None:

            if text is None:
                text = component_id

            element_id = component_id
            script = ''

        else:

            on_function_name = on_function.__name__
            off_function_name = off_function.__name__

            if text is None:
                text = f'{component_id} {on_function_name}/{off_function_name}'

            element_id = f'{component_id}-{on_function_name}-{off_function_name}'
            element_var = element_id.replace('-', '_')
            script = (
                f'\n<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'const {element_var} = $("#{element_id}");\n'
                f'{element_var}.on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: {element_var}.is(":checked") ? "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{on_function_name}" : "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{off_function_name}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>'
            )

        checked = ' checked ' if initially_on else ''

        return (
            element_id,
            (
                f'<div class="form-check form-switch switch-container">\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{element_id}"{checked}/>\n'
                f'  <label class="form-check-label" for="{element_id}">{text}</label>\n'                
                f'</div>'
                f'{script}'
            )
        )

    @staticmethod
    def get_range(
            component_id: str,
            min_value: int,
            max_value: int,
            step: int,
            initial_value: int,
            reset_to_initial_value_upon_release: bool,
            zero_range_upon_direction_change: bool,
            decrement_keys: List[str],
            increment_keys: List[str],
            reset_to_initial_value_keys: List[str],
            vertical: bool,
            on_input_function: Callable[[int], None],
            text: Optional[str],
            shift_sets_extreme: bool
    ) -> Tuple[str, str]:
        """
        Get range UI element.

        :param component_id: Component id.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step.
        :param initial_value: Initial value.
        :param reset_to_initial_value_upon_release: Whether to reset to the initial value upon release of the mouse
        button or touch gesture (whichever is being used).
        :param zero_range_upon_direction_change: Whether to zero the range upon change of direction. For example, if the
        range has a positive value and the decrement key is pressed, then the range will decrement from zero rather than
        from its current value.
        :param decrement_keys: Keyboard keys that decrement the range value.
        :param increment_keys: Keyboard keys that increment the range value.
        :param reset_to_initial_value_keys: Keyboard keys that reset the range to the initial value.
        :param vertical: Whether the range should be displayed vertically.
        :param on_input_function: Function to call when range value changes.
        :param text: Readable text to display.
        :param shift_sets_extreme: Whether holding shift while pressing an increment/decrement key sets the servo to its
        extreme value.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        on_input_function_name = on_input_function.__name__

        if text is None:
            text = f'{component_id} {on_input_function_name}'

        element_id = f'{component_id}-{on_input_function_name}'
        element_var = f'{element_id.replace("-", "_")}_element'
        range_var = f'{element_id.replace("-", "_")}_range'

        # get the parameter name to set
        non_self_params = [
            param_name
            for param_name, param in inspect.signature(on_input_function).parameters.items()
            if param_name != 'self' and str(param.default) == "<class 'inspect._empty'>"  # only consider params without default values
        ]
        if len(non_self_params) == 1:
            value_param = non_self_params[0]
        else:
            raise ValueError('Function for range must contain exactly 1 parameter.')

        vertical_style = ""
        if vertical:
            vertical_style = ' orient="vertical"'

        js_set_value_function_name = element_id.replace('-', '_')
        js_current_value = f'current_{value_param}'
        js_new_value = f'new_{value_param}'

        mouse_touch_release_event = ''
        if reset_to_initial_value_upon_release:
            mouse_touch_release_event = (
                f'{element_var}.on("mouseup touchend", function () {{\n'
                f'  {js_set_value_function_name}({initial_value}, true);\n'
                f'}});\n'
            )

        decrement_case = "\n".join([f'    case \"{k}\":' for k in decrement_keys])
        if decrement_case != '':

            decrement_zero_range = ''
            if zero_range_upon_direction_change:
                decrement_zero_range = (
                    f'      if ({js_current_value} > 0) {{\n'
                    f'        {js_current_value} = 1;\n'
                    f'      }}\n'
                )

            decrement_case += (
                f'\n'
                f'{decrement_zero_range}'
                f'      {js_new_value} = {js_current_value} - {step};\n'
                f'      break;\n'
            )

        decrement_shift_case = "\n".join([f'    case \"{k.upper()}\":' for k in decrement_keys if shift_sets_extreme])
        if decrement_shift_case != '':
            decrement_shift_case += (
                f'\n'
                f'      new_degrees = {min_value};\n'
                f'      break;\n'
            )

        increment_case = "\n".join([f'    case \"{k}\":' for k in increment_keys])
        if increment_case != '':

            increment_zero_range = ''
            if zero_range_upon_direction_change:
                increment_zero_range = (
                    f'      if ({js_current_value} < 0) {{\n'
                    f'        {js_current_value} = -1;\n'
                    f'      }}\n'
                )

            increment_case += (
                f'\n'
                f'{increment_zero_range}'
                f'      {js_new_value} = {js_current_value} + {step};\n'
                f'      break;\n'
            )

        increment_shift_case = "\n".join([f'    case \"{k.upper()}\":' for k in increment_keys if shift_sets_extreme])
        if increment_shift_case != '':
            increment_shift_case += (
                f'\n'
                f'      new_degrees = {max_value};\n'
                f'      break;\n'
            )

        reset_case = "\n".join([f'    case \"{k}\":' for k in reset_to_initial_value_keys])
        if reset_case != '':
            reset_case += (
                f'\n'
                f'      {js_new_value} = {initial_value};\n'
                f'      break;\n'
            )

        window_key_down_event_listener = ''
        if len(decrement_case) + len(increment_case) + len(reset_case) > 0:
            window_key_down_event_listener = (
                f'window.addEventListener("keydown", (event) => {{\n'
                f'  let {js_current_value} = parseInt({range_var}.value);\n'
                f'  let {js_new_value} = {js_current_value};\n'
                f'  switch (event.key) {{\n'
                f'{decrement_case}'
                f'{decrement_shift_case}'
                f'{increment_case}'
                f'{increment_shift_case}'
                f'{reset_case}'
                f'  }}\n'
                f'  if ({js_new_value} !== {js_current_value}) {{\n'
                f'    {js_set_value_function_name}({js_new_value}, true);\n'
                f'  }}\n'
                f'  event.preventDefault();\n'
                f'}}, true);\n'
            )

        window_key_up_event_listener = ''
        if shift_sets_extreme and len(increment_keys + decrement_keys) > 0:
            key_cases = "\n".join([f'    case \"{k.upper()}\":' for k in increment_keys + decrement_keys])
            window_key_up_event_listener = (
                f'window.addEventListener("keyup", (event) => {{\n'
                f'  let {js_current_value} = parseInt({range_var}.value);\n'
                f'  let {js_new_value} = {js_current_value};\n'
                f'  switch (event.key) {{\n'
                f'{key_cases}\n'
                f'      {js_new_value} = {initial_value};\n'
                f'      break;\n'
                f'  }}\n'
                f'  if ({js_new_value} !== {js_current_value}) {{\n'
                f'    {js_set_value_function_name}({js_new_value}, true);\n'
                f'  }}\n'
                f'  event.preventDefault();\n'
                f'}}, true);\n'
            )

        return (
            element_id,
            (
                f'<div class="range">\n'
                f'  <label for="{element_id}" class="form-label">{text}</label>\n'
                f'  <input type="range"{vertical_style} class="form-range" min="{min_value}" max="{max_value}" step="{step}" value="{initial_value}" id="{element_id}" />\n'
                f'</div>\n'
                f'<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'const {element_var} = $("#{element_id}");\n'
                f'const {range_var} = {element_var}[0];\n'
                f'function {js_set_value_function_name} ({value_param}, set_range) {{\n'
                f'  if ({value_param} < {min_value} || {value_param} > {max_value}) {{\n'
                f'    return;\n'
                f'  }}\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{on_input_function_name}?{value_param}=int:" + {value_param},\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'  if (set_range) {{\n'
                f'    {range_var}.value = {value_param};\n'
                f'  }}\n'
                f'}}\n'
                f'{element_var}.on("input", function () {{\n'
                f'  {js_set_value_function_name}({range_var}.value, false);\n'
                f'}});\n'
                f'{mouse_touch_release_event}'
                f'{window_key_down_event_listener}'
                f'{window_key_up_event_listener}'
                f'</script>'
            )
        )

    @staticmethod
    def get_range_html_attribute(
            element_id: str,
            element_attribute: str,
            min_value: int,
            max_value: int,
            step: int,
            initial_value: int,
            text: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get range UI element that sets an attribute on another HTML element.

        :param element_id: ID of element to set attribute for.
        :param element_attribute: Name of attribute to set.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step.
        :param initial_value: Initial value.
        :param text: Readable text to display.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        element_var = element_id.replace('-', '_')
        range_element_id = f'{element_id}-{element_attribute}'
        range_element_var = f'{range_element_id.replace("-", "_")}_element'
        range_var = f'{range_element_id.replace("-", "_")}_range'

        if text is None:
            text = range_element_id

        return (
            range_element_id,
            (
                f'<div class="range">\n'
                f'  <label for="{range_element_id}" class="form-label">{text}</label>\n'
                f'  <input type="range" class="form-range" min="{min_value}" max="{max_value}" step="{step}" value="{initial_value}" id="{range_element_id}" />\n'
                f'</div>\n'
                f'<script type="module">\n'
                f'const {element_var} = $("#{element_id}")[0];\n'
                f'const {range_element_var} = $("#{range_element_id}");\n'
                f'const {range_var} = {range_element_var}[0];\n'
                f'{range_element_var}.on("input", function () {{\n'
                f'  {element_var}.{element_attribute} = {range_var}.value\n'
                f'}});\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_label(
            component_id: str,
            function: Callable[[], Any],
            refresh_interval: timedelta,
            text: Optional[str],
            pause_for_checkbox_id: Optional[str],
            float_precision: Optional[int]
    ) -> Tuple[str, str]:
        """
        Get label that refreshes periodically.

        :param component_id: Component id.
        :param function: Function to call to obtain new value.
        :param refresh_interval: How long to wait between refresh calls.
        :param text: Readable text to display.
        :param pause_for_checkbox_id: HTML identifier of checkbox to pause for before getting label.
        :param float_precision: Floating-point precision to display, or None if the returned value is not a float or it
        should be displayed with full precision.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
        label_element = element_id.replace('-', '_')
        read_value_function_name = f'read_value_{element_id}'.replace('-', '_')

        if text is None:
            text = function_name

        pause_import_javascript = ''
        pause_element_javascript = ''
        pause_await_javascript = ''
        if pause_for_checkbox_id is not None:
            pause_import_javascript = 'import {is_checked} from "./utils.js";\n'
            pause_var_javascript = pause_for_checkbox_id.replace('-', '_')
            pause_element_javascript = f'const {pause_var_javascript} = $("#{pause_for_checkbox_id}");\n'
            pause_await_javascript = f'  await is_checked({pause_var_javascript});\n'

        float_precision_javascript = ''
        if float_precision is not None:
            float_precision_javascript = (
                f'      if (return_value !== null) {{\n'
                f'        return_value = return_value.toFixed({float_precision});\n'
                f'      }}\n'
            )

        return (
            element_id,
            (
                f'<div>\n'
                f'  <label id="{element_id}">{text}:  None</label>\n'
                f'</div>\n'
                f'<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'{pause_import_javascript}'
                f'const {label_element} = $("#{element_id}")[0];\n'
                f'{pause_element_javascript}'
                f'async function {read_value_function_name}() {{\n'
                f'{pause_await_javascript}'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'                
                f'{float_precision_javascript}'
                f'      if (return_value === null) {{\n'
                f'        return_value = "None";\n'
                f'      }}\n'
                f'      {label_element}.innerHTML = "{text}:  " + return_value;\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      await {read_value_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'      {label_element}.innerHTML = "{text}:  None";\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      await {read_value_function_name}();\n'
                f'    }}\n'
                f'  }});\n'
                f'}}\n'
                f'{read_value_function_name}();\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_image(
            component_id: str,
            width: int,
            refresh_function: Callable[[], Any],
            refresh_interval: Optional[timedelta],
            pause_for_checkbox_id: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get image that refreshes periodically.

        :param component_id: Component id.
        :param width: Initial width of HTML image.
        :param refresh_function: Function to call to obtain new image as a base-64 encoded byte string.
        :param refresh_interval: How long to wait between refresh calls, or None for no interval.
        :param pause_for_checkbox_id: HTML identifier of checkbox to pause for before capturing image.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        refresh_function_name = refresh_function.__name__
        element_id = f'{component_id}-{refresh_function_name}'
        latency_label_id = f'{component_id}-latency'
        latency_label_var = latency_label_id.replace('-', '_')
        capture_function_name = f'capture_{element_id}'.replace('-', '_')
        img_alt = element_id.replace('_', '-')
        image_element = element_id.replace('-', '_')

        refresh_interval_javascript = ''
        if refresh_interval is not None:
            refresh_interval_javascript = f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'

        pause_import_javascript = ''
        pause_element_javascript = ''
        pause_await_javascript = ''
        if pause_for_checkbox_id is not None:
            pause_import_javascript = 'import {is_checked} from "./utils.js";\n'
            pause_var_javascript = pause_for_checkbox_id.replace('-', '_')
            pause_element_javascript = f'const {pause_var_javascript} = $("#{pause_for_checkbox_id}");\n'
            pause_await_javascript = f'  await is_checked({pause_var_javascript});\n'

        return (
            element_id,
            (
                f'<div style="text-align: center">\n'
                f'  <img alt="{img_alt}" id="{element_id}" width="{width}" src="" />\n'
                f'  <label id="{latency_label_id}">Latency (ms):  None</label>\n'
                f'</div>\n'
                f'<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'{pause_import_javascript}'
                f'import {{init_latency, set_call_time, update_latency}} from "./utils.js";\n'
                f'const {latency_label_var} = $("#{latency_label_id}")[0];\n'
                f'init_latency("{latency_label_id}", 0.99);\n'
                f'const {image_element} = $("#{element_id}")[0];\n'
                f'{pause_element_javascript}'
                f'async function {capture_function_name}() {{\n'
                f'{pause_await_javascript}'
                f'  set_call_time("{latency_label_id}");\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{refresh_function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      {image_element}.src = "data:image/jpg;base64," + return_value;\n'
                f'      {latency_label_var}.innerHTML = "Latency (ms):  " + update_latency("{latency_label_id}").toFixed(0);\n'
                f'{refresh_interval_javascript}'
                f'      await {capture_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'{refresh_interval_javascript}'
                f'      await {capture_function_name}();\n'
                f'    }}\n'
                f'  }});\n'
                f'}}\n'
                f'{capture_function_name}();\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_query(
            args: Optional[Dict[str, Any]]
    ) -> str:
        """
        Get query string for a dictionary of arguments.

        :param args: Arguments.
        :return: Query string.
        """

        if args is not None and len(args) > 0:
            query = '&'.join([
                f'{arg_name}={type(arg_value).__name__}:{arg_value}'
                for arg_name, arg_value in args.items()
            ])
        else:
            query = ''

        return query

    class TextboxType(StrEnum):
        """
        Textbox types.
        """

        TEXT = 'text'
        EMAIL = 'email'
        NUMBER = 'number'
        PASSWORD = 'password'
        SEARCH = 'search'
        TELEPHONE = 'tel'
        URL = 'url'
        TEXT_AREA = 'textarea'

    @staticmethod
    def get_textbox(
            component_id: str,
            label: str,
            default_text: str,
            textbox_type: TextboxType
    ) -> Tuple[str, str]:
        """
        Get textbox.

        :param component_id: Component id.
        :param label: Label for textbox.
        :param default_text: Default text.
        :param textbox_type: Textbox type.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        element_id = component_id

        return (
            element_id,
            (
                f'<div class="form-outline" data-mdb-input-init>\n'
                f'  <input type="{textbox_type}" value="{default_text}" id="{element_id}" class="form-control active"/>\n'
                f'  <label class="form-label" for="{element_id}">{label}</label>\n'
                f'</div>'
            )
        )

    @staticmethod
    def get_action_button_list(
            component_id: str,
            refresh_function: Callable[[], List[Dict]],
            refresh_interval: Optional[timedelta],
            image_width: str,
            image_height: str,
            action_function_names: List[Tuple[Callable[[int], None], str]]
    ) -> Tuple[str, str]:
        """
        Get an action button list that refreshes its items periodically.

        https://mdbootstrap.com/docs/standard/components/list-group/

        :param component_id: Component id.
        :param refresh_function: Function called to obtain the list of action-button items. Each item in this list must
        have the following structure:

        {
            'image': [base-64 encoded string value of the image bytes],
            'title': [action title],
            'description': [action description]
        }

        :param refresh_interval: Time interval between list refreshes, or None to refresh as quickly as possible.
        :param image_width: Image width specifier (e.g., "100px").
        :param image_height: Image height specifier (e.g., "100px").
        :param action_function_names: List of 2-tuples of (1) function to call when an item's action is clicked (the
        function must take a single integer argument named `item_idx`), and (2) the name of the action.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        refresh_function_name = refresh_function.__name__
        element_id = f'{component_id}-{refresh_function_name}'
        refresh_items_function_name = f'refresh_items_{element_id}'.replace('-', '_')
        list_element = element_id.replace('-', '_')

        # build action links html event event-listener hookups
        action_links_html = ''
        action_links_add_event_listeners_js = ''
        for action_function, name in action_function_names:
            action_id = f'{element_id}-${{item_idx}}-{action_function.__name__}'
            action_links_html += f'<a class="btn btn-link btn-rounded btn-sm stacked-link" role="button" href="javascript:void(0);" id="{action_id}">{name}</a>'
            action_links_add_event_listeners_js += f'        document.getElementById(`{action_id}`).addEventListener("click", action_button_clicked);\n'

        refresh_interval_javascript = ''
        if refresh_interval is not None:
            refresh_interval_javascript = f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'

        return (
            element_id,
            (
                f'<div style="text-align: center">\n'
                f'  <ul class="list-group list-group-light list-unstyled" id="{element_id}">\n'
                f'  </ul>\n'
                f'</div>\n'
                f'<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'const {list_element} = document.getElementById("{element_id}");\n'
                f'function action_button_clicked(event) {{\n'
                f'  event.preventDefault();\n'
                f'  let clicked_id_parts = event.target.id.split("-");\n'
                f'  let clicked_index = clicked_id_parts.at(-2);\n'
                f'  let clicked_action_name = clicked_id_parts.at(-1);\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/" + clicked_action_name + "?item_idx=int:" + clicked_index,\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}}\n'
                f'async function {refresh_items_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{refresh_function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      let item_idx = 0;\n'
                f'      {list_element}.innerHTML = "";\n'
                f'      return_value.forEach(item => {{\n'                
                f'        const li = document.createElement("li");\n'
                f'        li.innerHTML = `'
                f'          <li class="list-group-item d-flex justify-content-between align-items-center">'
                f'            <div class="d-flex align-items-center">'
                f'              <img src="data:image/jpg;base64,${{item.image}}" alt="" style="width: {image_width}; height: {image_height}"/>'
                f'              <div class="ms-3">'
                f'                <p class="fw-bold mb-1">${{item.title}}</p>'
                f'                <p class="text-muted mb-0">${{item.description}}</p>'
                f'              </div>'                
                f'            </div>'
                f'            <div class="link-container">'
                f'{action_links_html}'
                f'            </div>'                
                f'          </li>`;\n'
                f'        {list_element}.appendChild(li);\n'
                f'{action_links_add_event_listeners_js}'
                f'        item_idx++;\n'
                f'      }});\n'
                f'{refresh_interval_javascript}'
                f'      await {refresh_items_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'{refresh_interval_javascript}'
                f'      await {refresh_items_function_name}();\n'
                f'    }}\n'
                f'  }});\n'
                f'}}\n'
                f'{refresh_items_function_name}();\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_javascript_for_accessing_dyn_arg_value(
            dyn_arg_type: Type,
            dyn_arg_comp_id: str
    ):
        """
        Get JavaScript for obtaining the value of an argument dynamically from a UI element.

        :param dyn_arg_type: Argument type.
        :param dyn_arg_comp_id: Component id.
        :return: JavaScript.
        """

        if dyn_arg_type in [int, float]:
            js = f'document.getElementById("{dyn_arg_comp_id}").value'  # assume number textbox
        elif dyn_arg_type == bool:
            js = f'$("#{dyn_arg_comp_id}").is(":checked")'  # assume switch
        else:
            raise ValueError(f'Unknown dynamic argument type:  {dyn_arg_type}')

        return js

    @staticmethod
    def get_button(
            component_id: str,
            pressed_function: Optional[Callable[..., Any]],
            pressed_args: Optional[Dict[str, Any]],
            pressed_dyn_args_name_type_id: Optional[List[Tuple[str, Type, str]]],
            released_function: Optional[Callable[..., Any]],
            released_args: Optional[Dict[str, Any]],
            key: Optional[str],
            text: Optional[str],
            element_id_suffix: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Get button.

        :param component_id: Component id.
        :param pressed_function: Function to call when the button is pressed.
        :param pressed_args: Dictionary of argument names/values to pass to `pressed_function`.
        :param pressed_dyn_args_name_type_id: Dynamic arguments that refer to other components whose values are obtained
        at runtime for the query string. List of 3-tuples of argument name, argument Python type, and UI component id.
        :param released_function: Function to call when the button is released.
        :param released_args: Dictionary of argument names/values to pass to `released_function`.
        :param key: Key that, when pressed/released, will trigger the associated functions.
        :param text: Readable text to display.
        :param element_id_suffix: Optional element id suffix to differentiate it.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        if pressed_function is None and released_function is None:
            raise ValueError('Either pressed or released function must be provided.')

        if text is None:
            text = component_id

        pressed_function_name = None if pressed_function is None else pressed_function.__name__
        released_function_name = None if released_function is None else released_function.__name__
        element_id = '-'.join(filter(
            None,
            [component_id, pressed_function_name, released_function_name, element_id_suffix]
        ))
        element_var = element_id.replace('-', '_')

        pressed_function_js = ''
        pressed_events_js = ''
        if pressed_function is not None:

            pressed_args_query = RpyFlask.get_query(pressed_args)

            if pressed_dyn_args_name_type_id is None:
                pressed_dyn_args_js = '  let dyn_args_query = "";\n'
            else:
                pressed_dyn_args_js = f'  let dyn_args_query = "{"" if pressed_args_query == "" else "&"}";\n'
                pressed_dyn_args_js += ''.join(
                    (
                        f'  {"let " if i == 0 else ""}dyn_arg_value = {RpyFlask.get_javascript_for_accessing_dyn_arg_value(dyn_arg_type, dyn_arg_comp_id)};\n'
                        f'  dyn_args_query = dyn_args_query + "{"" if i == 0 else "&"}{dyn_arg_name}={dyn_arg_type.__name__}:" + dyn_arg_value;\n'
                    )
                    for i, (dyn_arg_name, dyn_arg_type, dyn_arg_comp_id) in enumerate(pressed_dyn_args_name_type_id)
                )

            pressed_function_name_js = f'on_press_{pressed_function_name}'
            pressed_function_js = (
                f'function {pressed_function_name_js} () {{\n'
                f'{pressed_dyn_args_js}'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{pressed_function_name}?{pressed_args_query}" + dyn_args_query,\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}}\n'
            )
            pressed_events_js = (
                f'{element_var}.on("mousedown touchstart", function () {{\n'
                f'  {pressed_function_name_js}();\n'
                f'}});\n'
            )

            if key is not None:

                if 'Meta' in key:
                    switch_value = 'event.code'
                else:
                    switch_value = 'event.key'

                pressed_events_js += (
                    f'window.addEventListener("keydown", (event) => {{\n'
                    f'  switch ({switch_value}) {{\n'
                    f'    case "{key}":\n'
                    f'      {pressed_function_name_js}();\n'
                    f'      break;\n'
                    f'  }}\n'
                    f'  event.preventDefault();\n'
                    f'}}, true);\n'
                )

        released_function_js = ''
        released_events_js = ''
        if released_function is not None:
            released_args_query = RpyFlask.get_query(released_args)
            released_function_name_js = f'on_release_{released_function_name}'
            released_function_js = (
                f'function {released_function_name_js} () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{released_function_name}?{released_args_query}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}}\n'
            )
            released_events_js = (
                f'{element_var}.on("mouseup touchend", function () {{\n'
                f'  {released_function_name_js}();\n'
                f'}});\n'
            )

            if key is not None:

                if 'Meta' in key:
                    switch_value = 'event.code'
                else:
                    switch_value = 'event.key'

                released_events_js += (
                    f'window.addEventListener("keyup", (event) => {{\n'
                    f'  switch ({switch_value}) {{\n'
                    f'    case "{key}":\n'
                    f'      {released_function_name_js}();\n'
                    f'      break;\n'
                    f'  }}\n'
                    f'  event.preventDefault();\n'
                    f'}}, true);\n'
                )

        return (
            element_id,
            (
                f'<button type="button" class="btn btn-primary" id="{element_id}">{text}</button>\n'
                f'<script type="module">\n'
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'const {element_var} = $("#{element_id}");\n'
                f'{pressed_function_js}'
                f'{pressed_events_js}'
                f'{released_function_js}'                
                f'{released_events_js}'
                f'</script>'
            )
        )

    @staticmethod
    def get_repeater(
            component_id: str,
            function: Callable[[], Any],
            refresh_interval: timedelta
    ) -> Tuple[str, str]:
        """
        Get a script that periodically calls a function.

        :param component_id: Component id.
        :param function: Function to call to obtain new value.
        :param refresh_interval: How long to wait between refresh calls.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
        js_function_name = f'{element_id}'.replace('-', '_')

        return (
            element_id,
            (
                f'import {{rest_host, rest_port}} from "./globals.js";\n'
                f'async function {js_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (_) {{\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      await {js_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      await {js_function_name}();\n'
                f'    }}\n'
                f'  }});\n'
                f'}}\n'
                f'{js_function_name}();'
            )
        )

    @staticmethod
    def get_mjpg_streamer(
            component_id: str,
            height: int,
            refresh_interval: Optional[timedelta],
            pause_for_checkbox_id: Optional[str],
            port: int
    ):
        """
        Get connection to the mjpg_streamer application.

        :param component_id: Component id.
        :param height: Height of image.
        :param refresh_interval: How long to wait between refresh calls, or None for no interval.
        :param pause_for_checkbox_id: HTML identifier of checkbox to pause for before capturing image.
        :param port: Port that mjpg_streamer runs on.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        element_id = f'{component_id}-mjpg_streamer'
        image_element = element_id.replace('-', '_')
        insert_new_image_function_name = f'insert_new_image_{image_element}'

        refresh_interval_javascript = ''
        if refresh_interval is not None:
            refresh_interval_javascript = f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'

        pause_import_javascript = ''
        pause_element_javascript = ''
        pause_await_javascript = ''
        if pause_for_checkbox_id is not None:
            pause_import_javascript = 'import {is_checked} from "./utils.js";\n'
            pause_var_javascript = pause_for_checkbox_id.replace('-', '_')
            pause_element_javascript = f'const {pause_var_javascript} = $("#{pause_for_checkbox_id}");\n'
            pause_await_javascript = f'  await is_checked({pause_var_javascript});\n'

        return (
            element_id,
            (
                f'<div style="height:{height}px;display:flex;justify-content:center" id="{element_id}"></div>\n'
                f'<script type="module">\n'
                f'import {{rest_host}} from "./globals.js";\n'
                f'{pause_import_javascript}'
                f'{pause_element_javascript}'
                f'let image_id = 0;\n'
                f'let loaded_images = [];\n'                
                f'async function {insert_new_image_function_name}() {{\n'
                f'{pause_await_javascript}'
                f'  let img = new Image();\n'
                f'  img.style.position = "absolute";\n'
                f'  img.style.zIndex = "-1";\n'
                f'  img.onload = image_loaded;\n'
                f'  img.onerror = image_error;\n'
                f'  img.src = "http://" + rest_host + ":{port}/?action=snapshot&n=" + (++image_id);\n'
                f'  let {image_element} = document.getElementById("{element_id}");\n'
                f'  {image_element}.insertBefore(img, {image_element}.firstChild);\n'
                f'{refresh_interval_javascript}'
                f'}}\n'
                f'async function image_loaded() {{\n'
                f'  this.style.zIndex = image_id;\n'
                f'  while (1 < loaded_images.length) {{\n'
                f'    let image_to_remove = loaded_images.shift();\n'
                f'    image_to_remove.parentNode.removeChild(image_to_remove);\n'
                f'  }}\n'
                f'  loaded_images.push(this);\n'
                f'  await {insert_new_image_function_name}();\n'
                f'}}\n'
                f'async function image_error() {{\n'
                f'  await new Promise(r => setTimeout(r, 500.0));\n'
                f'  await {insert_new_image_function_name}();\n'
                f'}}\n'
                f'{insert_new_image_function_name}();\n'
                f'</script>'
            )
        )


app = RpyFlask(__name__)

# add the special call history component, which tracks rest calls.
call_history = CallHistory()
call_history.id = 'app-call-history'
app.add_component(call_history)
app.load_state()

# allow cross-site access from an html front-end
CORS(app)

# hook atexit to the app's callback and to clean up
atexit.register(app.on_exit)
atexit.register(cleanup)

# set up gpio
setup()


@app.route('/list')
def list_components() -> Response:
    """
    List available components.

    :return: Dictionary of components by id and string.
    """

    response = flask.jsonify({
        component_id: str(component)
        for component_id, component in app.id_component.items()
    })

    return response


@app.route('/call/<string:component_id>/<string:function_name>', methods=['GET'])
def call(
        component_id: str,
        function_name: str
) -> Response:
    """
    Call a function on a component.

    :param component_id: Component id.
    :param function_name: Name of function to call.
    :return: Function value.
    """

    if component_id not in app.id_component:
        abort(HTTPStatus.NOT_FOUND, f'No component with id {component_id}.')

    arg_value = {}
    add_to_history = False
    for arg_name, type_value_str in request.args.to_dict().items():

        type_str, value_str = type_value_str.split(':', maxsplit=1)
        value = CALL_TYPE_CAST_FUNCTIONS[type_str](value_str)

        # the add_to_history argument pertains to the rest application and indicates whether the call should be recorded
        # in the history. use it here and do not pass is to the function we're going to call.
        if arg_name == 'add_to_history' and isinstance(value, bool):
            add_to_history = value
        else:
            arg_value[arg_name] = value

    call_reference = Call(component_id, function_name, arg_value)
    response, _ = call_reference.execute()

    if add_to_history:
        call_history.add(call_reference)

    return response


def write_component_files_cli(
        args: Optional[List[str]] = None
):
    """
    Write component files for an application.

    :param args: CLI arguments, or None to use sys.argv.
    """

    if args is None:
        args = sys.argv[1:]

    arg_parser = ArgumentParser(description='Write component files for an application.')

    arg_parser.add_argument(
        '--app',
        type=str,
        help='Name of module containing the raspberry-py REST application to write component files for. Can either be the fully-qualified name or a name relative to the current working directory within the package.'
    )

    arg_parser.add_argument(
        '--rest-host',
        type=str,
        default='localhost',
        help='Host serving the raspberry-py REST application.'
    )

    arg_parser.add_argument(
        '--rest-port',
        type=int,
        default=5000,
        help='Port serving the raspberry-py REST application.'
    )

    arg_parser.add_argument(
        '--dir-path',
        type=str,
        help='Path in which to write the component files. Will be created if it does not exist.'
    )

    parsed_args = arg_parser.parse_args(args)

    # get the app module and attribute name
    app_args = parsed_args.app.split(':')
    app_module_name = app_args[0]
    app_name = 'app'
    if len(app_args) == 2:
        app_name = app_args[1]
    elif len(app_args) > 2:
        raise ValueError(f'Invalid app argument:  {parsed_args.app}')

    # load module and app
    app_to_write: Optional[RpyFlask] = None
    for prefix in [''] + [f'{s}.' for s in list(reversed(os.getcwd().split(os.sep))) if s != '']:

        app_module_name = f'{prefix}{app_module_name}'

        try:
            app_module = importlib.import_module(app_module_name)
            print(f'Checking module {app_module_name} for {app_name}.')
        except ModuleNotFoundError:
            continue

        if hasattr(app_module, app_name):
            app_to_write = getattr(app_module, app_name)
            print(f'Found {app_name} in module {app_module_name}')
            break
        else:
            print(f'Did not find {app_name} in module {app_module_name}')

    if app_to_write is None:
        print(f'Failed to find {app_name} in {parsed_args.app}. Nothing to write.')
    else:
        app_to_write.write_component_files(
            rest_host=parsed_args.rest_host,
            rest_port=parsed_args.rest_port,
            dir_path=expanduser(parsed_args.dir_path)
        )
