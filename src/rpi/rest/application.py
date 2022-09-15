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

from rpi.gpio import Component
from rpi.gpio.lights import LED
from rpi.gpio.motors import DcMotor, Servo, Stepper
from rpi.gpio.sensors import Thermistor, Photoresistor
from rpi.gpio.sounds import ActiveBuzzer


class RpiFlask(Flask):
    """
    Extension of Flask that adds RPI GPIO components.
    """

    def add_component(
            self,
            component: Component
    ):
        """
        Add component to the app.

        :param component: Component.
        """

        self.components[component.id] = component

    def write_ui_elements(
            self,
            host: str,
            port: int,
            dir_path: str
    ):
        """
        Write UI elements for RPI components in the current Flask application.

        :param host: Host serving the Flask application.
        :param port: Port serving the Flask application.
        :param dir_path: Directory in which to write UI element files (will be created if it does not exist).
        """

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        for component in self.components.values():
            for element_id, element in self.get_ui_elements(component, host, port):
                path = join(dir_path, f'{element_id}.html')
                with open(path, 'w') as component_file:
                    component_file.write(f'{element}\n')
                print(f'Wrote {path}')

    @staticmethod
    def get_ui_elements(
            component: Component,
            host: str,
            port: int,
    ) -> List[Tuple[str, str]]:
        """
        Get UI elements for a component.

        :param component: Component.
        :param host: Host serving the Flask application.
        :param port: Port serving the Flask application.
        :return: List of 2-tuples of (1) element keys and (2) UI elements for the component.
        """

        if isinstance(component, LED):
            elements = [
                RpiFlask.get_switch(component.id, host, port, component.turn_on, component.turn_off)
            ]
        elif isinstance(component, DcMotor):
            elements = [
                RpiFlask.get_switch(component.id, host, port, component.start, component.stop),
                RpiFlask.get_range(component.id, -100, 100, 1, host, port, component.set_speed)
            ]
        elif isinstance(component, Servo):
            elements = [
                RpiFlask.get_switch(component.id, host, port, component.start, component.stop),
                RpiFlask.get_range(component.id, 0, 180, 1, host, port, component.set_degrees)
            ]
        elif isinstance(component, Stepper):
            elements = [
                RpiFlask.get_switch(component.id, host, port, component.start, component.stop)
            ]
        elif isinstance(component, Photoresistor):
            elements = [
                RpiFlask.get_label(component.id, host, port, component.get_light_level, timedelta(seconds=1))
            ]
        elif isinstance(component, Thermistor):
            elements = [
                RpiFlask.get_label(component.id, host, port, component.get_temperature_f, timedelta(seconds=1))
            ]
        elif isinstance(component, ActiveBuzzer):
            elements = [
                RpiFlask.get_button(component.id, host, port, component.buzz, 'duration=seconds:0.5')
            ]
        else:
            raise ValueError(f'Unknown component type:  {type(component)}')

        return elements

    @staticmethod
    def get_switch(
            component_id: str,
            host: str,
            port: int,
            on_function: Callable[[], None],
            off_function: Callable[[], None]
    ) -> Tuple[str, str]:
        """
        Get switch UI element.

        :param component_id: Component id.
        :param host: Host.
        :param port: Port.
        :param on_function: Function to call when switch is flipped on.
        :param off_function: Function to call when switch is flipped off.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        on_function_name = on_function.__name__
        off_function_name = off_function.__name__

        element_id = f'{component_id}-{on_function_name}-{off_function_name}'

        return (
            element_id,
            (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{element_id}">{component_id} {on_function_name}/{off_function_name}</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{element_id}" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{element_id}").on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: $("#{element_id}").is(":checked") ? "http://{host}:{port}/call/{component_id}/{on_function_name}" : "http://{host}:{port}/call/{component_id}/{off_function_name}",\n'
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
            host: str,
            port: int,
            on_input_function: Callable[[int], None]
    ) -> Tuple[str, str]:
        """
        Get range UI element.

        :param component_id: Component id.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step.
        :param host: Host.
        :param port: Port.
        :param on_input_function: Function to call when range value changes.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        on_input_function_name = on_input_function.__name__

        element_id = f'{component_id}-{on_input_function_name}'

        non_self_params = [k for k, v in inspect.signature(on_input_function).parameters.items() if k != 'self']
        if len(non_self_params) != 1:
            raise ValueError('Function for range must contain exactly 1 parameter.')

        on_input_param = non_self_params[0]

        return (
            element_id,
            (
                f'<div class="range">\n'
                f'  <label for="{element_id}" class="form-label">{component_id} {on_input_function_name}</label>\n'
                f'  <input type="range" class="form-range" min="{min_value}" max="{max_value}" step="{step}" id="{element_id}" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{element_id}").on("input", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{host}:{port}/call/{component_id}/{on_input_function_name}?{on_input_param}=int:" + $("#{element_id}")[0].value,\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>'
            )
        )

    @staticmethod
    def get_label(
            component_id: str,
            host: str,
            port: int,
            function: Callable[[], Any],
            refresh_interval: timedelta
    ) -> Tuple[str, str]:
        """
        Get label that refreshes periodically.

        :param component_id: Component id.
        :param host: Host.
        :param port: Port.
        :param function: Function to call to obtain new value.
        :param refresh_interval: How long to wait between refresh calls.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'
        read_value_function_name = f'read_value_{element_id}'.replace('-', '_')

        return (
            element_id,
            (
                f'<div>\n'
                f'  <label id="{element_id}">{function_name}:  N/A</label>\n'
                f'</div>\n'
                f'<script>\n'
                f'function {read_value_function_name}() {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{host}:{port}/call/{component_id}/{function_name}",\n'
                f'    type: "GET",\n'
                f'    success: async function (return_value) {{\n'
                f'      document.getElementById("{element_id}").innerHTML = "{function_name}:  " + return_value;\n'
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
    def get_button(
            component_id: str,
            host: str,
            port: int,
            function: Callable[[], Any],
            query: Optional[str]
    ) -> Tuple[str, str]:
        """
        Get button.

        :param component_id: Component id.
        :param host: Host.
        :param port: Port.
        :param function: Function to call.
        :param query: Query to submit with function call, or None for no query.
        :return: 2-tuple of (1) element id and (2) UI element.
        """

        if query is not None and len(query) > 0:
            query = f"?{query}"
        else:
            query = ""

        function_name = function.__name__
        element_id = f'{component_id}-{function_name}'

        return (
            element_id,
            (
                f'<button type="button" class="btn btn-primary" id="{element_id}">{component_id}</button>\n'
                f'<script>\n'
                f'$("#{element_id}").click(function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{host}:{port}/call/{component_id}/{function_name}{query}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>'
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

        self.components = {}


app = RpiFlask(__name__)


@app.route('/list')
def list_components() -> Response:
    """
    List available components.

    :return: Dictionary of components by id and string.
    """

    response = flask.jsonify({
        component_id: str(component)
        for component_id, component in app.components.items()
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
    :return: State of component after calling the specified function.
    """

    if component_id not in app.components:
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

    component = app.components[component_id]
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
        help='Fully-qualified module containing the RPI REST application to write component files for.'
    )

    arg_parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host serving the RPI REST application.'
    )

    arg_parser.add_argument(
        '--port',
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
    app_to_write = None
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
        app_to_write.write_ui_elements(
            host=parsed_args.host,
            port=parsed_args.port,
            dir_path=expanduser(parsed_args.dir_path)
        )
