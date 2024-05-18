from inspect import isasyncgen, isgenerator, iscoroutine
from types import FunctionType
from typing import Callable, Any

from StdioBridge.api._response import Response, StreamResponse
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

    def add_router(self, path: list[str], router: '_Router'):
        if len(path) == 1:
            if path[0] not in self._routes:
                self._routes[path[0]] = router
                router.name = path[0]
            else:
                raise KeyError(f'Router "{path[0]}" is already registered.')
        else:
            if path[0] not in self._routes:
                self._routes[path[0]] = _Router(path[0])
            next_router = self._routes[path[0]]
            new_path = path[1:]
            next_router.add_router(new_path, router)

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


class Router:
    def __init__(self):
        self._router = _Router('/')

    def _method(self, method: str, url: str):
        def decorator(func: FunctionType) -> Callable:
            async def wrapper(data: dict[str: Any],
                              path_params: dict[str: str] = None,
                              query_params: dict[str: list[str]] = None) -> Response | StreamResponse:
                params = dict()
                try:
                    for param_name, param_type in func.__annotations__.items():
                        if param_type == dict:
                            if data is not None:
                                params[param_name] = param_type(data)
                        elif path_params and param_name in path_params:
                            params[param_name] = param_type(path_params[param_name])
                        elif query_params and param_name in query_params:
                            if param_type != list:
                                if len(query_params[param_name]) == 1:
                                    params[param_name] = param_type(query_params[param_name][0])
                                else:
                                    raise InternalServerError
                            else:
                                params[param_name] = param_type(query_params[param_name])
                except ValueError:
                    raise ErrorUnprocessableEntity()

                try:
                    res = func(**params)
                    if isasyncgen(res) or isgenerator(res):
                        return StreamResponse(res)
                    elif iscoroutine(res):
                        res = await res
                    return Response(200, res)
                except ApiError as e:
                    raise e
                except Exception as e:
                    raise InternalServerError(f"{e.__class__.__name__}: {e}")

            self._add(method, url, wrapper)

            return wrapper

        return decorator

    def get(self, url: str):
        return self._method('get', url)

    def post(self, url: str):
        return self._method('post', url)

    def put(self, url: str):
        return self._method('put', url)

    def delete(self, url: str):
        return self._method('delete', url)

    def patch(self, url: str):
        return self._method('patch', url)

    def _add(self, method, url: str, func):
        self._router.add(url.strip('/').split('/'), method, func)

    def add_router(self, url: str, router: 'Router'):
        self._router.add_router(url.strip('/').split('/'), router._router)

    def found(self, path: str, method: str):
        return self._router.found(path.strip('/').split('/'), method)
