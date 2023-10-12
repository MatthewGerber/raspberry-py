import importlib
import inspect
import os.path
import sys
from argparse import ArgumentParser
from datetime import timedelta
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional, Tuple, Callable, Any, Union

import flask
from flask import Flask, request, abort, Response
from flask_cors import CORS

from raspberry_py.gpio import Component, setup
from raspberry_py.gpio.freenove.smart_car import Car
from raspberry_py.gpio.lights import LED
from raspberry_py.gpio.motors import DcMotor, Servo, Stepper
from raspberry_py.gpio.power import Relay
from raspberry_py.gpio.robotics import RaspberryPyArm, RaspberryPyElevator
from raspberry_py.gpio.sensors import Thermistor, Photoresistor, UltrasonicRangeFinder, Camera, MjpgStreamer, Tachometer
from raspberry_py.gpio.sounds import ActiveBuzzer

LEFT_ARROW_KEYS = ['Left', 'ArrowLeft']
RIGHT_ARROW_KEYS = ['Right', 'ArrowRight']
UP_ARROW_KEYS = ['Up', 'ArrowUp']
DOWN_ARROW_KEYS = ['Down', 'ArrowDown']
SPACE_KEY = [' ']


class RpyFlask(Flask):
    """
    Extension of Flask that adds raspberry-py GPIO components.
    """

    def add_component(
            self,
            component: Component,
            write: bool
    ):
        """
        Add a component to the app. Any component that needs to be reached via REST API must be added to the app.

        :param component: Component.
        :param write: Whether to write component files when write_component_files is called from the command line.
        """

        self.id_component[component.id] = component

        if write:
            self.components_to_write.append(component)

        # add certain components recursively, but do not write the component files for them. the write_component_files
        # function handles the generation of html/javascript elements for these components in a particular way.
        if (
            isinstance(component, Car) or
            isinstance(component, RaspberryPyArm)
        ):
            for component in component.get_components():
                self.add_component(component, False)

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

        for component in self.components_to_write:
            for element_id, element_content in self.get_ui_elements(component):

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
    def get_ui_elements(
            component: Component
    ) -> List[Tuple[Union[str, Tuple[str, str]], str]]:
        """
        Get UI elements for a component.

        :param component: Component.
        :return: List of 2-tuples of (1) element keys and (2) element content for the component.
        """

        if isinstance(component, LED):
            elements = [
                RpyFlask.get_switch(component.id, component.turn_on, component.turn_off, None, component.is_on())
            ]
        elif isinstance(component, Relay):
            elements = [
                RpyFlask.get_switch(component.id, component.close, component.open, None, False)
            ]
        elif isinstance(component, DcMotor):
            curr_state: DcMotor.State = component.state
            elements = [
                RpyFlask.get_switch(component.id, component.start, component.stop, None, curr_state.on),
                RpyFlask.get_range(component.id, component.min_speed, component.max_speed, 1, component.get_speed(), False, False, [], [], [], False, component.set_speed, None, False)
            ]
        elif isinstance(component, Servo):
            curr_state: Servo.State = component.state
            elements = [
                RpyFlask.get_switch(component.id, component.start, component.stop, None, curr_state.on),
                RpyFlask.get_range(component.id, int(component.min_degree), int(component.max_degree), 1, int(component.get_degrees()), False, False, [], [], [], False, component.set_degrees, None, False)
            ]
        elif isinstance(component, Stepper):
            elements = [
                RpyFlask.get_switch(component.id, component.start, component.stop, None, False)
            ]
        elif isinstance(component, Photoresistor):
            elements = [
                RpyFlask.get_label(component.id, component.get_light_level, timedelta(seconds=1), None, None, None)
            ]
        elif isinstance(component, Tachometer):
            elements = [
                RpyFlask.get_label(component.id, component.get_rps, timedelta(seconds=1), None, None, None)
            ]
        elif isinstance(component, Thermistor):
            elements = [
                RpyFlask.get_label(component.id, component.get_temperature_f, timedelta(seconds=1), None, None, None)
            ]
        elif isinstance(component, UltrasonicRangeFinder):
            elements = [
                RpyFlask.get_label(component.id, component.measure_distance_once, timedelta(seconds=1), None, None, None)
            ]
        elif isinstance(component, ActiveBuzzer):
            elements = [
                RpyFlask.get_button(component.id, component.buzz, None, component.stop, None, None, None)
            ]
        elif isinstance(component, Camera):
            elements = [
                RpyFlask.get_image(component.id, component.width, component.capture_image, timedelta(seconds=1.0 / component.fps), None)
            ]
        elif isinstance(component, Car):

            power_id, power_element = RpyFlask.get_switch(component.id, component.start, component.stop, 'Power', component.on)

            elements = [
                RpyFlask.get_range(component.camera_pan_servo.id, int(component.camera_pan_servo.min_degree), int(component.camera_pan_servo.max_degree), 3, int(component.camera_pan_servo.get_degrees()), False, False, ['s'], ['f'], ['r'], False, component.camera_pan_servo.set_degrees, 'Pan', True),
                RpyFlask.get_range(component.camera_tilt_servo.id, int(component.camera_tilt_servo.min_degree), int(component.camera_tilt_servo.max_degree), 3, int(component.camera_tilt_servo.get_degrees()), False, False, ['d'], ['e'], ['r'], False, component.camera_tilt_servo.set_degrees, 'Tilt', True),
                RpyFlask.get_range(component.id, component.min_speed, component.max_speed, 1, 0, True, False, DOWN_ARROW_KEYS, UP_ARROW_KEYS, SPACE_KEY, True, component.set_speed, '', False),
                RpyFlask.get_range(component.id, int(component.wheel_min_speed / 2.0), int(component.wheel_max_speed / 2.0), 1, 0, True, True, RIGHT_ARROW_KEYS, LEFT_ARROW_KEYS, SPACE_KEY, True, component.set_differential_speed, '', False),
                RpyFlask.get_label(component.range_finder.id, component.range_finder.measure_distance_once, timedelta(seconds=1), 'Range (cm)', power_id, 1),
                RpyFlask.get_button(component.buzzer.id, component.buzzer.buzz, None, component.buzzer.stop, None, 'h', 'Horn'),
                (power_id, power_element),
                RpyFlask.get_switch(component.id, component.enable_face_tracking, component.disable_face_tracking, 'Face Tracking', component.track_faces),
                RpyFlask.get_switch(component.id, component.enable_light_tracking, component.disable_light_tracking, 'Light Tracking', component.track_light),
                RpyFlask.get_label(component.id, component.get_battery_percent, timedelta(seconds=10), 'Battery (%)', power_id, 1)
            ]

            if isinstance(component.camera, Camera):
                camera_id, camera_element = RpyFlask.get_image(component.camera.id, component.camera.width, component.camera.capture_image, None, power_id)
                camera_elements = [
                    (camera_id, camera_element),
                    RpyFlask.get_range_html_attribute(camera_id, 'width', 100, 800, 10, component.camera.width, 'Display Size '),
                    RpyFlask.get_range(component.camera.id, 1, 5, 1, 1, False, False, [], [], [], False, component.camera.multiply_resolution, 'Display Resolution', False),
                    RpyFlask.get_switch(component.camera.id, component.camera.enable_face_detection, component.camera.disable_face_detection, 'Face Detection', component.camera.run_face_detection),
                    RpyFlask.get_switch(component.camera.id, component.camera.enable_face_circles, component.camera.disable_face_circles, 'Face Circles', component.camera.circle_detected_faces)
                ]
                elements.extend(camera_elements)
            elif isinstance(component.camera, MjpgStreamer):
                elements.append(RpyFlask.get_mjpg_streamer(component.camera.id, component.camera.height, None, power_id, component.camera.port))
            else:
                raise ValueError(f'Unknown camera:  {component.camera}')

            if component.connection_blackout_tolerance_seconds is not None:
                blackout_id, blackout_element = RpyFlask.get_repeater(component.id, component.connection_heartbeat, timedelta(seconds=component.connection_blackout_tolerance_seconds / 4.0))
                elements.append(((blackout_id, 'js'), blackout_element))

        elif isinstance(component, RaspberryPyArm):
            elements = [
                RpyFlask.get_range(component.base_rotator_servo.id, int(component.base_rotator_servo.min_degree), int(component.base_rotator_servo.max_degree), 1, int(component.base_rotator_servo.get_degrees()), False, False, ['j'], ['k'], ['p'], False, component.base_rotator_servo.set_degrees, 'Base', False),
                RpyFlask.get_range(component.arm_elevator_servo.id, int(component.arm_elevator_servo.min_degree), int(component.arm_elevator_servo.max_degree), 1, int(component.arm_elevator_servo.get_degrees()), False, False, ['u'], ['m'], ['p'], False, component.arm_elevator_servo.set_degrees, 'Arm Elevation', False),
                RpyFlask.get_range(component.wrist_elevator_servo.id, int(component.wrist_elevator_servo.min_degree), int(component.wrist_elevator_servo.max_degree), 1, int(component.wrist_elevator_servo.get_degrees()), False, False, ['i'], [','], ['p'], False, component.wrist_elevator_servo.set_degrees, 'Wrist Elevation', False),
                RpyFlask.get_range(component.wrist_rotator_servo.id, int(component.wrist_rotator_servo.min_degree), int(component.wrist_rotator_servo.max_degree), 1, int(component.wrist_rotator_servo.get_degrees()), False, False, ['l'], [';'], ['p'], False, component.wrist_rotator_servo.set_degrees, 'Wrist Rotation', False),
                RpyFlask.get_range(component.pinch_servo.id, int(component.pinch_servo.min_degree), int(component.pinch_servo.max_degree), 1, int(component.pinch_servo.get_degrees()), False, False, ['.'], ['o'], ['p'], False, component.pinch_servo.set_degrees, 'Pinch', False)
            ]

        elif isinstance(component, RaspberryPyElevator):
            elements = [
                RpyFlask.get_button(component.id, component.move_up_1_mm_1_sec, None, None, None, 'MetaRight', 'Move up'),
                RpyFlask.get_button(component.id, component.move_down_1_mm_1_sec, None, None, None, 'MetaLeft', 'Move down')
            ]
        else:
            raise ValueError(f'Unknown component type:  {type(component)}')

        return elements

    @staticmethod
    def get_switch(
            component_id: str,
            on_function: Callable[[], None],
            off_function: Callable[[], None],
            text: Optional[str],
            initially_on: bool
    ) -> Tuple[str, str]:
        """
        Get switch UI element.

        :param component_id: Component id.
        :param on_function: Function to call when switch is flipped on.
        :param off_function: Function to call when switch is flipped off.
        :param text: Readable text to display.
        :param initially_on: Initially on.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        on_function_name = on_function.__name__
        off_function_name = off_function.__name__

        if text is None:
            text = f'{component_id} {on_function_name}/{off_function_name}'

        element_id = f'{component_id}-{on_function_name}-{off_function_name}'
        element_var = element_id.replace('-', '_')
        checked = ' checked ' if initially_on else ''

        return (
            element_id,
            (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{element_id}">{text}</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{element_id}"{checked}/>\n'
                f'</div>\n'
                f'<script type="module">\n'
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
            function: Callable[[], Any],
            refresh_interval: Optional[timedelta],
            pause_for_checkbox_id: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get image that refreshes periodically.

        :param component_id: Component id.
        :param width: Initial width of HTML image.
        :param function: Function to call to obtain new image.
        :param refresh_interval: How long to wait between refresh calls, or None for no interval.
        :param pause_for_checkbox_id: HTML identifier of checkbox to pause for before capturing image.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
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
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{function_name}",\n'
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
    def get_button(
            component_id: str,
            pressed_function: Optional[Callable[[], Any]],
            pressed_query: Optional[str],
            released_function: Optional[Callable[[], Any]],
            released_query: Optional[str],
            key: Optional[str],
            text: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get button.

        :param component_id: Component id.
        :param pressed_function: Function to call when the button is pressed.
        :param pressed_query: Query to submit with pressed_function call, or None for no query.
        :param released_function: Function to call when the button is released.
        :param released_query: Query to submit with released_function call, or None for no query.
        :param key: Key that, when pressed/released, will trigger the associated functions.
        :param text: Readable text to display.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        if pressed_function is None and released_function is None:
            raise ValueError('Either pressed or released function must be provided.')

        if text is None:
            text = component_id

        pressed_function_name = None if pressed_function is None else pressed_function.__name__
        released_function_name = None if released_function is None else released_function.__name__
        element_id = '-'.join(filter(None, [component_id, pressed_function_name, released_function_name]))
        element_var = element_id.replace('-', '_')

        pressed_function_js = ''
        pressed_events_js = ''
        if pressed_function is not None:

            if pressed_query is not None and len(pressed_query) > 0:
                pressed_query = f'?{pressed_query}'
            else:
                pressed_query = ''

            pressed_function_name_js = f'on_press_{pressed_function_name}'
            pressed_function_js = (
                f'function {pressed_function_name_js} () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{pressed_function_name}{pressed_query}",\n'
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

            if released_query is not None and len(released_query) > 0:
                released_query = f'?{released_query}'
            else:
                released_query = ''

            released_function_name_js = f'on_release_{released_function_name}'
            released_function_js = (
                f'function {released_function_name_js} () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://" + rest_host + ":" + rest_port + "/call/{component_id}/{released_function_name}{released_query}",\n'
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
        self.components_to_write = []


app = RpyFlask(__name__)

# allow cross-site access from an html front-end
CORS(app)

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

    arg_types = {
        'int': int,
        'str': str,
        'float': float,
        'days': lambda days: timedelta(days=float(days)),
        'hours': lambda hours: timedelta(hours=float(hours)),
        'minutes': lambda minutes: timedelta(minutes=float(minutes)),
        'seconds': lambda seconds: timedelta(seconds=float(seconds)),
        'milliseconds': lambda milliseconds: timedelta(milliseconds=float(milliseconds))
    }

    arg_value = {}
    for arg_name, type_value_str in request.args.to_dict().items():
        type_str, value_str = type_value_str.split(':', maxsplit=1)
        arg_value[arg_name] = arg_types[type_str](value_str)

    component = app.id_component[component_id]
    if hasattr(component, function_name):
        f = getattr(component, function_name)
        return flask.jsonify(f(**arg_value))
    else:
        abort(HTTPStatus.NOT_FOUND, f'Component {component} (id={component_id}) does not have a function named {function_name}.')


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
