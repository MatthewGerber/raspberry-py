import importlib
import os.path
import sys
from argparse import ArgumentParser
from http import HTTPStatus
from os.path import join, expanduser
from typing import List, Optional

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
            with open(join(dir_path, f'{component.id}.html'), 'w') as component_file:
                component_file.write(f'{self.get_html(component, host, port)}')

    @staticmethod
    def get_html(
            component: Component,
            host: str,
            port: int,
    ) -> str:
        """
        Get HTML for a component, including the UI elements and client-side JavaScript for handling UI events.

        :param component: Component.
        :param host: Host serving the Flask application.
        :param port: Port serving the Flask application.
        :return: HTML.
        """

        if isinstance(component, LED):
            return (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{component.id}">{component.id}</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{component.id}" />\n'                
                f'</div>\n'
                f'<script>\n'
                f'$("#{component.id}").on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: $("#{component.id}").is(":checked") ? "http://{host}:{port}/call/{component.id}/turn_on" : "http://{host}:{port}/call/{component.id}/turn_off",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>\n'
            )
        elif isinstance(component, DcMotor):
            return (
                f'<div class="form-check form-switch">\n'
                f'  <label class="form-check-label" for="{component.id}-start-stop">{component.id} on/off</label>\n'
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{component.id}-start-stop" />\n'
                f'</div>\n'
                f'<div class="range">\n'
                f'  <label for="{component.id}-speed" class="form-label">{component.id} speed</label>\n'
                f'  <input type="range" class="form-range" min="-100" max="100" step="1" id="{component.id}-speed" />\n'
                f'</div>\n'
                f'<script>\n'
                f'$("#{component.id}-start-stop").on("change", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: $("#{component.id}-start-stop").is(":checked") ? "http://{host}:{port}/call/{component.id}/start" : "http://{host}:{port}/call/{component.id}/stop",\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'$("#{component.id}-speed").on("input", function () {{\n'
                f'  $.ajax({{\n'
                f'    url: "http://{host}:{port}/call/{component.id}/set_speed?speed=int:" + $("#{component.id}-speed")[0].value,\n'
                f'    type: "GET"\n'
                f'  }});\n'
                f'}});\n'
                f'</script>\n'
            )
        else:
            raise ValueError(f'Unknown component type:  {type(component)}')

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


def write_component_files(
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
