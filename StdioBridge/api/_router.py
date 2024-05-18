from inspect import isasyncgen, isgenerator, iscoroutine
from types import FunctionType, GenericAlias
from typing import Callable, Any, Type

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


def _convert_param(param_type: Type, param):
    try:
        return param_type(param)
    except Exception:
        raise ErrorUnprocessableEntity(f"Cannot convert {param} to {param_type.__name__}")


def _result_to_json(result):
    if isinstance(result, dict):
        return {key: _result_to_json(value) for key, value in result.items()}
    if isinstance(result, list):
        return [_result_to_json(el) for el in result]
    if hasattr(result, 'dict'):
        return result.dict()
    if hasattr(result, 'json'):
        return result.json()
    return result


class Router:
    def __init__(self):
        self._router = _Router('/')

    @staticmethod
    def _check_data_param(data, param_type):
        if param_type == dict:
            return dict(data)
        if isinstance(param_type, GenericAlias) and param_type.__origin__ == dict:
            return dict(data)
        try:
            import pydantic
            if issubclass(param_type, pydantic.BaseModel):
                return param_type(**data)
        except Exception:
            pass
        return None

    @staticmethod
    def _check_query_param(param_list, param_type):
        if param_type == list:
            return list(param_list)
        elif isinstance(param_type, GenericAlias) and param_type.__origin__ == list:
            if len(param_type.__args__) != 1:
                raise ErrorUnprocessableEntity(f"Invalid param type: {param_type}")
            return [_convert_param(param_type.__args__[0], el) for el in param_list]
        else:
            if len(param_list) == 1:
                return _convert_param(param_type, param_list[0])
            else:
                raise ErrorUnprocessableEntity("Only one param is allowed")

    def _method(self, method: str, url: str):
        def decorator(func: FunctionType) -> Callable:
            async def wrapper(data: dict[str: Any],
                              path_params: dict[str: str],
                              query_params: dict[str: list[str]]) -> Response | StreamResponse:
                params = dict()

                for param_name, param in path_params.items():
                    param_type = func.__annotations__.get(param_name, Any)
                    params[param_name] = _convert_param(param_type, param)

                for param_name, param in query_params.items():
                    if param_name in path_params:
                        raise ErrorUnprocessableEntity(f"Duplicate param name: '{param_name}'")
                    param_type = func.__annotations__.get(param_name, Any)
                    params[param_name] = self._check_query_param(param, param_type)

                for param_name, param_type in func.__annotations__.items():
                    if param_name in path_params or param_name in query_params:
                        continue
                    elif (p := self._check_data_param(data, param_type)) is not None:
                        params[param_name] = p

                try:
                    res = func(**params)
                    if isasyncgen(res) or isgenerator(res):
                        return StreamResponse(res)
                    elif iscoroutine(res):
                        res = await res
                    return Response(200, _result_to_json(res))
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
