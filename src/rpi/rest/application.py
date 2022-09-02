from http import HTTPStatus

import flask
from flask import Flask, request, abort, Response

from rpi.gpio import Component

app = Flask(__name__)

__components__ = {}


def add_component(
        component: Component
):
    """
    Add component to the app.

    :param component: Component.
    """

    __components__[component.id] = component


@app.route('/list')
def list_components() -> Response:
    """
    List available components.

    :return: Dictionary of components by id and string.
    """

    response = flask.jsonify({
        component_id: str(component)
        for component_id, component in __components__.items()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
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

    if component_id not in __components__:
        abort(HTTPStatus.NOT_FOUND, f'No component with id {component_id}.')

    args = request.args.to_dict()

    component = __components__[component_id]
    if hasattr(component, function_name):
        f = getattr(component, function_name)
        f(**args)
        response = flask.jsonify(component.get_state().__dict__)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        abort(HTTPStatus.NOT_FOUND, f'Component {component} (id={component_id}) does not have a function named {function_name}.')
