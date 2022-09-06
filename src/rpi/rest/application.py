import importlib
import os.path
import sys
from argparse import ArgumentParser
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional, Tuple

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

    def write_component_html_files(
            self,
            host: str,
            port: int,
            dir_path: str
    ):
        """
        Write component HTML files in the current Flask application.

        :param host: Host serving the Flask application.
        :param port: Port serving the Flask application.
        :param dir_path: Directory in which to write component HTML files (will be created if it does not exist).
        """

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        for component in self.components.values():
            element_id, html_js = self.get_html_js(component, host, port)
            with open(join(dir_path, f'{element_id}.html'), 'w') as component_file:
                component_file.write(html_js)

    @staticmethod
    def get_html_js(
            component: Component,
            host: str,
            port: int,
    ) -> List[Tuple[str, str]]:
        """
        Get HTML for a component, including the UI elements and client-side JavaScript for handling UI events.

        :param component: Component.
        :param host: Host serving the Flask application.
        :param port: Port serving the Flask application.
        :return: List of 2-tuples of (1) element keys and (2) HTML/JavaScript elements for the components.
        """

        if isinstance(component, LED):
            return [
                RpiFlask.get_switch_html_js(component.id, host, port, 'turn_on', 'turn_off')
            ]
        elif isinstance(component, DcMotor):
            return [
                RpiFlask.get_switch_html_js(component.id, host, port, 'start', 'stop'),
                RpiFlask.get_range_html_js(component.id, -100, 100, 1, host, port, 'set_speed', 'speed')
            ]
        else:
            raise ValueError(f'Unknown component type:  {type(component)}')

    @staticmethod
    def get_switch_html_js(
            switch_id: str,
            host: str,
            port: int,
            on_function: str,
            off_function: str
    ) -> Tuple[str, str]:
        """
        Get switch HTML/JavaScript.

        :param switch_id: Switch id.
        :param host: Host.
        :param port: Port.
        :param on_function: On function name.
        :param off_function: Off function name.
        :return: 2-tuple of (1) id and (2) HTML/JavaScript.
        """

        element_id = f'{switch_id}-{on_function}-{off_function}'

        return (
            element_id,
            (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{element_id}">{switch_id} {on_function}/{off_function}</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{element_id}" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{element_id}").on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: $("#{element_id}").is(":checked") ? "http://{host}:{port}/call/{switch_id}/{on_function}" : "http://{host}:{port}/call/{switch_id}/{off_function}",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>\n'
            )
        )

    @staticmethod
    def get_range_html_js(
            range_id: str,
            min_value: int,
            max_value: int,
            step: int,
            host: str,
            port: int,
            on_input_function: str,
            on_input_param: str
    ) -> Tuple[str, str]:
        """
        Get range HTML/JavaScript.

        :param range_id: Range id.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step.
        :param host: Host.
        :param port: Port.
        :param on_input_function: On input function name.
        :param on_input_param: On input parameter name.
        :return: 2-tuple of (1) id and (2) HTML/JavaScript.
        """

        element_id = f'{range_id}-{on_input_function}'

        return (
            element_id,
            (
                f'<div class="range">\n'
                f'  <label for="{element_id}" class="form-label">{range_id} {on_input_function}</label>\n'
                f'  <input type="range" class="form-range" min="{min_value}" max="{max_value}" step="{step}" id="{element_id}" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{element_id}").on("input", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{host}:{port}/call/{range_id}/{on_input_function}?{on_input_param}=int:" + $("#{element_id}")[0].value,\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>\n'
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

    app_to_write.write_component_html_files(
        host=args.host,
        port=args.port,
        dir_path=expanduser(args.dir_path)
    )
