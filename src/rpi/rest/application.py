import os.path
from http import HTTPStatus
from os.path import join

import flask
from flask import Flask, request, abort, Response

from rpi.gpio import Component
from rpi.gpio.lights import LED


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
                f'  <input class="form-check-input" type="checkbox" role="switch" id="{component.id}" />\n'
                f'  <label class="form-check-label" for="{component.id}">{component.id}</label>\n'
                f'  <script>\n'
                f'    $("#{component.id}").on("change", function () {{\n'
                f'      $.ajax({{\n'
                f'        url: $("#{component.id}").is(":checked") ? "http://{host}:{port}/call/{component.id}/turn_on" : "http://{host}:{port}/call/{component.id}/turn_off",\n'
                f'        type: "GET"\n'
                f'      }});\n'
                f'    }});\n'
                f'  </script>\n'
                f'</div>\n'
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
