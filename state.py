from typing import Any, Callable

class GlobalState:
    def __init__(self):
        self._attribute = None
        self._callback = None

    @property
    def attribute(self):
        return self._attribute

    @attribute.setter
    def attribute(self, value):
        self._attribute = value
        if self._callback:
            self._callback(value)

    def set_callback(self, callback_func):
        self._callback = callback_func

def useGlobalState():
    state = GlobalState()

    def getGlobalState():
        return state.attribute
    
    def setCallback(cb: Callable[[Any],Any]):
        state.set_callback(cb)

    def setGlobalState(value: Any):
        state.attribute = value

    return getGlobalState, setGlobalState, setCallback