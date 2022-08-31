from typing import Dict

from flask import Flask, request, abort
from http import HTTPStatus

from rpi.gpio import Component

__app__ = Flask(__name__)
__components__ = {}


def get() -> Flask:
    """
    Get the Flask app.

    :return: Flask app.
    """

    return __app__


def add_component(
        component: Component
):
    """
    Add component to the app.

    :param component: Component.
    """

    __components__[component.id] = component


@__app__.route('/list')
def list_components() -> Dict[str, str]:
    """
    List available components.

    :return: Dictionary of components by id and string.
    """

    return {
        component_id: str(component)
        for component_id, component in __components__.items()
    }


@__app__.route('/call/<string:component_id>/<string:function_name>', methods=['GET'])
def call(
        component_id: str,
        function_name: str
) -> Dict:
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
        return component.get_state().__dict__
    else:
        abort(HTTPStatus.NOT_FOUND, f'Component {component} (id={component_id}) does not have a function named {function_name}.')
