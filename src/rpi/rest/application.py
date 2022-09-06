import importlib
import inspect
import os.path
import sys
from argparse import ArgumentParser
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional, Tuple, Callable

import flask
from flask import Flask, request, abort, Response

from rpi.gpio import Component
from rpi.gpio.lights import LED
from rpi.gpio.motors import DcMotor


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
                with open(join(dir_path, f'{element_id}.html'), 'w') as component_file:
                    component_file.write(f'{element}\n')

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
                RpiFlask.get_switch(component.id, host, port, LED.turn_on, LED.turn_off)
            ]
        elif isinstance(component, DcMotor):
            elements = [
                RpiFlask.get_switch(component.id, host, port, DcMotor.start, DcMotor.stop),
                RpiFlask.get_range(component.id, -100, 100, 1, host, port, DcMotor.set_speed)
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
        'float': float
    }

    args = {
        n: arg_types[t.split(':')[0]](t.split(':')[1])
        for n, t in request.args.to_dict().items()
    }

    component = app.components[component_id]
    if hasattr(component, function_name):
        f = getattr(component, function_name)
        f(**args)
        response = flask.jsonify(component.get_state().__dict__)
        return response
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

    args = arg_parser.parse_args(args)

    # get the app module and attribute name
    app_args = args.app.split(':')
    app_module_name = app_args[0]
    app_name = None
    if len(app_args) == 2:
        app_name = app_args[1]
    elif len(app_args) > 2:
        raise ValueError(f'Invalid app argument:  {args.app}')

    # load module and app
    app_module = importlib.import_module(app_module_name)
    if app_name is None and hasattr(app_module, 'app'):
        app_to_write = getattr(app_module, 'app')
    elif app_name is not None and hasattr(app_module, app_name):
        app_to_write = getattr(app_module, app_name)
    else:
        raise ValueError(f'Module {app_module_name} does not contain an "app" attribute, and no other name is specified.')

    app_to_write.write_ui_elements(
        host=args.host,
        port=args.port,
        dir_path=expanduser(args.dir_path)
    )
