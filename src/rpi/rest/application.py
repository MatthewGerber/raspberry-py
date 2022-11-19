import importlib
import inspect
import os.path
import sys
from argparse import ArgumentParser
from datetime import timedelta
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional, Tuple, Callable, Any

import flask
from flask import Flask, request, abort, Response
from flask_cors import CORS

from rpi.gpio import Component, setup
from rpi.gpio.freenove.smart_car import Car
from rpi.gpio.lights import LED
from rpi.gpio.motors import DcMotor, Servo, Stepper
from rpi.gpio.sensors import Thermistor, Photoresistor, UltrasonicRangeFinder, Camera
from rpi.gpio.sounds import ActiveBuzzer

LEFT_ARROW_KEYS = ['Left', 'ArrowLeft']
RIGHT_ARROW_KEYS = ['Right', 'ArrowRight']
UP_ARROW_KEYS = ['Up', 'ArrowUp']
DOWN_ARROW_KEYS = ['Down', 'ArrowDown']
SPACE_KEY = [' ']


class RpiFlask(Flask):
    """
    Extension of Flask that adds RPI GPIO components.
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

        # add car components recursively, but do not write the component files for them. the write_component_files
        # function handles writing car components in a particular way.
        if isinstance(component, Car):
            for car_component in component.get_components():
                self.add_component(car_component, False)

    def write_component_files(
            self,
            rest_host: str,
            rest_port: int,
            dir_path: str
    ):
        """
        Write files for RPI components in the current application.

        :param rest_host: Host serving the REST application.
        :param rest_port: Port serving the REST application.
        :param dir_path: Directory in which to write files (will be created if it does not exist).
        """

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        for component in self.components_to_write:
            for element_id, element_content in self.get_ui_elements(component, rest_host, rest_port):
                path = join(dir_path, f'{element_id}.html')
                with open(path, 'w') as component_file:
                    component_file.write(f'{element_content}\n')
                print(f'Wrote {path}')

    @staticmethod
    def get_ui_elements(
            component: Component,
            rest_host: str,
            rest_port: int,
    ) -> List[Tuple[str, str]]:
        """
        Get UI elements for a component.

        :param component: Component.
        :param rest_host: Host serving the REST application.
        :param rest_port: Port serving the REST application.
        :return: List of 2-tuples of (1) element keys and (2) element content for the component.
        """

        if isinstance(component, LED):
            elements = [
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.turn_on, component.turn_off, None, component.is_on())
            ]
        elif isinstance(component, DcMotor):
            elements = [
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.start, component.stop, None, component.state.on),
                RpiFlask.get_range(component.id, component.min_speed, component.max_speed, 1, component.get_speed(), False, False, [], [], [], False, rest_host, rest_port, component.set_speed, None)
            ]
        elif isinstance(component, Servo):
            elements = [
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.start, component.stop, None, component.state.on),
                RpiFlask.get_range(component.id, int(component.min_degree), int(component.max_degree), 1, int(component.get_degrees()), False, False, [], [], [], False, rest_host, rest_port, component.set_degrees, None)
            ]
        elif isinstance(component, Stepper):
            elements = [
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.start, component.stop, None, False)
            ]
        elif isinstance(component, Photoresistor):
            elements = [
                RpiFlask.get_label(component.id, rest_host, rest_port, component.get_light_level, timedelta(seconds=1), None)
            ]
        elif isinstance(component, Thermistor):
            elements = [
                RpiFlask.get_label(component.id, rest_host, rest_port, component.get_temperature_f, timedelta(seconds=1), None)
            ]
        elif isinstance(component, UltrasonicRangeFinder):
            elements = [
                RpiFlask.get_label(component.id, rest_host, rest_port, component.measure_distance_once, timedelta(seconds=1), None)
            ]
        elif isinstance(component, ActiveBuzzer):
            elements = [
                RpiFlask.get_button(component.id, rest_host, rest_port, component.buzz, None, component.stop, None, None)
            ]
        elif isinstance(component, Camera):
            elements = [
                RpiFlask.get_image(component.id, component.width, rest_host, rest_port, component.capture_image, timedelta(seconds=1.0 / component.fps))
            ]
        elif isinstance(component, Car):

            camera_id, camera_element = RpiFlask.get_image(component.camera.id, component.camera.width, rest_host, rest_port, component.camera.capture_image, None)

            elements = [
                (camera_id, camera_element),
                RpiFlask.get_range(component.camera_pan_servo.id, int(component.camera_pan_servo.min_degree), int(component.camera_pan_servo.max_degree), 3, int(component.camera_pan_servo.get_degrees()), False, False, ['s'], ['f'], ['r'], False, rest_host, rest_port, component.camera_pan_servo.set_degrees, 'Pan'),
                RpiFlask.get_range(component.camera_tilt_servo.id, int(component.camera_tilt_servo.min_degree), int(component.camera_tilt_servo.max_degree), 3, int(component.camera_tilt_servo.get_degrees()), False, False, ['d'], ['e'], ['r'], False, rest_host, rest_port, component.camera_tilt_servo.set_degrees, 'Tilt'),
                RpiFlask.get_range_html_attribute(camera_id, 'width', 100, 800, 10, component.camera.width, 'Display Size '),
                RpiFlask.get_range(component.camera.id, 1, 5, 1, 1, False, False, [], [], [], False, rest_host, rest_port, component.camera.multiply_resolution, 'Display Resolution'),
                RpiFlask.get_range(component.id, component.min_speed, component.max_speed, 1, 0, True, False, DOWN_ARROW_KEYS, UP_ARROW_KEYS, SPACE_KEY, True, rest_host, rest_port, component.set_speed, ''),
                RpiFlask.get_range(component.id, int(component.wheel_min_speed / 2.0), int(component.wheel_max_speed / 2.0), 1, 0, True, True, RIGHT_ARROW_KEYS, LEFT_ARROW_KEYS, SPACE_KEY, True, rest_host, rest_port, component.set_differential_speed, ''),
                RpiFlask.get_label(component.range_finder.id, rest_host, rest_port, component.range_finder.measure_distance_once, timedelta(seconds=1), 'Range'),
                RpiFlask.get_button(component.buzzer.id, rest_host, rest_port, component.buzzer.buzz, None, component.buzzer.stop, None, 'Horn'),
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.start, component.stop, 'Power', component.on),
                RpiFlask.get_switch(component.camera.id, rest_host, rest_port, component.camera.enable_face_detection, component.camera.disable_face_detection, 'Face Detection', component.camera.run_face_detection),
                RpiFlask.get_switch(component.camera.id, rest_host, rest_port, component.camera.enable_face_circles, component.camera.disable_face_circles, 'Face Circles', component.camera.circle_detected_faces),
                RpiFlask.get_switch(component.id, rest_host, rest_port, component.enable_face_tracking, component.disable_face_tracking, 'Face Tracking', component.camera.track_faces)
            ]

            if component.connection_blackout_tolerance_seconds is not None:
                elements.append(RpiFlask.get_repeater(component.id, rest_host, rest_port, component.connection_heartbeat, timedelta(seconds=component.connection_blackout_tolerance_seconds / 4.0)))

        else:
            raise ValueError(f'Unknown component type:  {type(component)}')

        return elements

    @staticmethod
    def get_switch(
            component_id: str,
            rest_host: str,
            rest_port: int,
            on_function: Callable[[], None],
            off_function: Callable[[], None],
            text: Optional[str],
            initially_on: bool
    ) -> Tuple[str, str]:
        """
        Get switch UI element.

        :param component_id: Component id.
        :param rest_host: Host.
        :param rest_port: Port.
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

        checked = ' checked ' if initially_on else ''

        return (
            element_id,
            (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{element_id}">{text}</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{element_id}"{checked}/>\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{element_id}").on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: $("#{element_id}").is(":checked") ? "http://{rest_host}:{rest_port}/call/{component_id}/{on_function_name}" : "http://{rest_host}:{rest_port}/call/{component_id}/{off_function_name}",\n'
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
            rest_host: str,
            rest_port: int,
            on_input_function: Callable[[int], None],
            text: Optional[str]
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
        :param rest_host: Host.
        :param rest_port: Port.
        :param on_input_function: Function to call when range value changes.
        :param text: Readable text to display.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        on_input_function_name = on_input_function.__name__

        if text is None:
            text = f'{component_id} {on_input_function_name}'

        element_id = f'{component_id}-{on_input_function_name}'

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

        release_event = ''
        if reset_to_initial_value_upon_release:
            release_event = (
                f'$("#{element_id}").on("mouseup touchend", function () {{\n'
                f'  {js_set_value_function_name}({initial_value}, true);\n'
                f'}});\n'
            )

        decrement_case = "\n".join([f'    case \"{k}\":' for k in decrement_keys])
        if decrement_case != '':

            decrement_zero_range = ''
            if zero_range_upon_direction_change:
                decrement_zero_range = (
                    f'      if ({js_current_value} > 0) {{\n'
                    f'        {js_current_value} = 0;\n'
                    f'      }}\n'
                )

            decrement_case += (
                f'\n'
                f'{decrement_zero_range}'
                f'      {js_set_value_function_name}({js_current_value} - {step}, true);\n'
                f'      break;\n'
            )

        increment_case = "\n".join([f'    case \"{k}\":' for k in increment_keys])
        if increment_case != '':

            increment_zero_range = ''
            if zero_range_upon_direction_change:
                increment_zero_range = (
                    f'      if ({js_current_value} < 0) {{\n'
                    f'        {js_current_value} = 0;\n'
                    f'      }}\n'
                )

            increment_case += (
                f'\n'
                f'{increment_zero_range}'
                f'      {js_set_value_function_name}({js_current_value} + {step}, true);\n'
                f'      break;\n'
            )

        reset_case = "\n".join([f'    case \"{k}\":' for k in reset_to_initial_value_keys])
        if reset_case != '':
            reset_case += (
                f'\n'
                f'      {js_set_value_function_name}({initial_value}, true);\n'
                f'      break;\n'
            )

        window_event_listener = ''
        if len(decrement_case) + len(increment_case) + len(reset_case) > 0:
            window_event_listener = (
                f'window.addEventListener("keydown", (event) => {{\n'
                f'  {js_current_value} = parseInt($("#{element_id}")[0].value);\n'
                f'  switch (event.key) {{\n'
                f'{decrement_case}'
                f'{increment_case}'
                f'{reset_case}'
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
                f'<script>\n'
                f'function {js_set_value_function_name} ({value_param}, set_range) {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{on_input_function_name}?{value_param}=int:" + {value_param},\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'  if (set_range) {{\n'
                f'    $("#{element_id}")[0].value = {value_param};\n'
                f'  }}\n'
                f'}}\n'
                f'$("#{element_id}").on("input", function () {{\n'
                f'  {js_set_value_function_name}($("#{element_id}")[0].value, false);\n'
                f'}});\n'
                f'{release_event}'
                f'{window_event_listener}'
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

        range_element_id = f'{element_id}-{element_attribute}'

        if text is None:
            text = range_element_id

        return (
            range_element_id,
            (
                f'<div class="range">\n'
                f'  <label for="{range_element_id}" class="form-label">{text}</label>\n'
                f'  <input type="range" class="form-range" min="{min_value}" max="{max_value}" step="{step}" value="{initial_value}" id="{range_element_id}" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{range_element_id}").on("input", function () {{\n'
                f'  document.getElementById("{element_id}").{element_attribute} = $("#{range_element_id}")[0].value\n'
                f'}});\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_label(
            component_id: str,
            rest_host: str,
            rest_port: int,
            function: Callable[[], Any],
            refresh_interval: timedelta,
            text: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get label that refreshes periodically.

        :param component_id: Component id.
        :param rest_host: Host.
        :param rest_port: Port.
        :param function: Function to call to obtain new value.
        :param refresh_interval: How long to wait between refresh calls.
        :param text: Readable text to display.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
        read_value_function_name = f'read_value_{element_id}'.replace('-', '_')

        if text is None:
            text = function_name

        return (
            element_id,
            (
                f'<div>\n'
                f'  <label id="{element_id}">{text}:  null</label>\n'
                f'</div>\n'
                f'<script>\n'
                f'function {read_value_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      document.getElementById("{element_id}").innerHTML = "{text}:  " + return_value;\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      {read_value_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'      document.getElementById("{element_id}").innerHTML = "{text}:  null";\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      {read_value_function_name}();\n'
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
            rest_host: str,
            rest_port: int,
            function: Callable[[], Any],
            refresh_interval: Optional[timedelta]
    ) -> Tuple[str, str]:
        """
        Get image that refreshes periodically.

        :param component_id: Component id.
        :param width: Initial width of HTML image.
        :param rest_host: Host.
        :param rest_port: Port.
        :param function: Function to call to obtain new image.
        :param refresh_interval: How long to wait between refresh calls, or None for no interval.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
        capture_function_name = f'capture_{element_id}'.replace('-', '_')

        refresh_interval_javascript = ''
        if refresh_interval is not None:
            refresh_interval_javascript = f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'

        return (
            element_id,
            (
                f'<div style="text-align: center">\n'
                f'  <img id="{element_id}" width="{width}" src="" />\n'
                f'</div>\n'
                f'<script>\n'
                f'function {capture_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      document.getElementById("{element_id}").src = "data:image/jpg;base64," + return_value;\n'
                f'{refresh_interval_javascript}'
                f'      {capture_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'{refresh_interval_javascript}'
                f'      {capture_function_name}();\n'
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
            rest_host: str,
            rest_port: int,
            pressed_function: Optional[Callable[[], Any]],
            pressed_query: Optional[str],
            released_function: Optional[Callable[[], Any]],
            released_query: Optional[str],
            text: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get button.

        :param component_id: Component id.
        :param rest_host: Host.
        :param rest_port: Port.
        :param pressed_function: Function to call when the button is pressed.
        :param pressed_query: Query to submit with pressed_function call, or None for no query.
        :param released_function: Function to call when the button is released.
        :param released_query: Query to submit with released_function call, or None for no query.
        :param text: Readable text to display.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        if text is None:
            text = component_id

        element_id = component_id

        pressed_event = ''
        if pressed_function is not None:

            pressed_function_name = pressed_function.__name__
            if pressed_query is not None and len(pressed_query) > 0:
                pressed_query = f'?{pressed_query}'
            else:
                pressed_query = ''

            pressed_event = (
                f'$("#{element_id}").on("mousedown touchstart", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{pressed_function_name}{pressed_query}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
            )

        released_event = ''
        if released_function is not None:

            released_function_name = released_function.__name__
            if released_query is not None and len(released_query) > 0:
                released_query = f'?{released_query}'
            else:
                released_query = ''

            released_event = (
                f'$("#{element_id}").on("mouseup touchend", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{released_function_name}{released_query}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
            )

        return (
            element_id,
            (
                f'<button type="button" class="btn btn-primary" id="{element_id}">{text}</button>\n'
                f'<script>\n'
                f'{pressed_event}'
                f'{released_event}'
                f'</script>'
            )
        )

    @staticmethod
    def get_repeater(
            component_id: str,
            rest_host: str,
            rest_port: int,
            function: Callable[[], Any],
            refresh_interval: timedelta
    ) -> Tuple[str, str]:
        """
        Get a script that periodically calls a function.

        :param component_id: Component id.
        :param rest_host: Host.
        :param rest_port: Port.
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
                f'function {js_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{rest_host}:{rest_port}/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      {js_function_name}();\n'
                f'    }},\n'
                f'    error: async function(xhr, error){{\n'
                f'      console.log(error);\n'
                f'      await new Promise(r => setTimeout(r, {refresh_interval.total_seconds() * 1000}));\n'
                f'      {js_function_name}();\n'
                f'    }}\n'
                f'  }});\n'
                f'}}\n'
                f'{js_function_name}();'
            )
        )

    def __init__(
            self,
            import_name: str
    ):
        """
        Initialize the RpiFlask.

        :param import_name: Import name. See Flask documentation.
        """

        super().__init__(import_name=import_name)

        self.id_component = {}
        self.components_to_write = []


app = RpiFlask(__name__)

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
        help='Name of module containing the RPI REST application to write component files for. Can either be the fully-qualified name or a name relative to the current working directory within the package.'
    )

    arg_parser.add_argument(
        '--rest-host',
        type=str,
        default='localhost',
        help='Host serving the RPI REST application.'
    )

    arg_parser.add_argument(
        '--rest-port',
        type=int,
        default=5000,
        help='Port serving the RPI REST application.'
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
    app_to_write: Optional[RpiFlask] = None
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
