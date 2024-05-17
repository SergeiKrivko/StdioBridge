from typing import Callable

from StdioBridge.api.errors import *


class _Router:
    def __init__(self, name):
        self.name = name
        self._routes: dict[str: _Router] = dict()
        self._handlers: dict[str: Callable] = {}

    def add(self, path: list[str], method, func: Callable):
        if not path:
            if method not in self._handlers:
                self._handlers[method] = func
            else:
                raise KeyError(f'Method "{method}" is already registered.')
        else:
            param = None if not path[0].startswith('{') else path[0].strip('{}')
            if path[0] not in self._routes:
                self._routes[None if param else path[0]] = _Router(param or path[0])
            router = self._routes[None if param else path[0]]
            new_path = path[1:]
            router.add(new_path, method, func)

    def found(self, path: list[str], method: str):
        return self._found(path, method, dict())

    def _found(self, path: list[str], method: str, path_params: dict):
        method_not_found = False
        if not path:
            if method not in self._handlers:
                raise ErrorMethodNotAllowed()
            else:
                return self._handlers[method], path_params
        else:
            name, path = path[0], path[1:]
            if name in self._routes:
                try:
                    return self._routes[name]._found(path, method, path_params)
                except ErrorNotFound:
                    pass
                except ErrorMethodNotAllowed:
                    method_not_found = True
            if None in self._routes:
                try:
                    path_params[self._routes[None].name] = name
                    return self._routes[None]._found(path, method, path_params)
                except ErrorNotFound:
                    path_params.pop(self._routes[None].name)
                except ErrorMethodNotAllowed:
                    path_params.pop(self._routes[None].name)
                    method_not_found = True
        if method_not_found:
            raise ErrorMethodNotAllowed()
        raise ErrorNotFound()
