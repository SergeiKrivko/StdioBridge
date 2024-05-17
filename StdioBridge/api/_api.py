import asyncio
import json
from inspect import isgenerator, iscoroutine, isasyncgen
from types import FunctionType
from typing import Callable, Any
from urllib.parse import urlparse, parse_qs

from aioconsole import ainput

from StdioBridge.api._response import Response, StreamResponse
from StdioBridge.api._router import _Router
from StdioBridge.api.errors import *


class Api:
    def __init__(self):
        self._root_router = _Router('/')

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

            self.add(method, url, wrapper)

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

    def add(self, method, url: str, func):
        self._root_router.add(url.split('/'), method, func)

    async def _process_request(self, request: dict) -> Response:
        try:
            resp_id = request.get('id')
            url = request['url']
            method = request['method']
            data = request['data']
            stream = request.get('stream', False)
        except KeyError:
            raise ErrorBadRequest("Missing 'url', 'method', or 'data' key")

        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        url = parsed_url._replace(query="").geturl()

        func, path_params = self._root_router.found(url.split('/'), method)
        res = await func(data, path_params, query)

        if isinstance(res, StreamResponse):
            if not stream:
                lst = []
                async for chunk in res:
                    lst.append(chunk)
                print('!response!', json.dumps({'id': resp_id, 'code': res.code, 'data': lst}), sep='')
            else:
                started = False
                async for el in res:
                    if not started:
                        print('!stream_start!', json.dumps({'id': resp_id, 'code': res.code}), sep='')
                        started = True
                    print('!stream_chunk!', json.dumps({'id': resp_id, 'chunk': el}), sep='')
                print('!stream_end!', json.dumps({'id': resp_id, 'code': res.code}), sep='')
        else:
            if stream:
                print('!stream_start!', json.dumps({'id': resp_id, 'code': 400}), sep='')
                print('!stream_chunk!', json.dumps({'id': resp_id, 'chunk': "Stream not supported!"}), sep='')
            else:
                print('!response!', json.dumps({'id': resp_id, 'code': res.code, 'data': res.data}), sep='')

        return res

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        while True:
            try:
                inp = await ainput()
                data = json.loads(inp)
                resp_id = data.get('id')
            except json.JSONDecodeError:
                print("Invalid JSON")
            else:
                try:
                    await self._process_request(data)
                except ApiError as err:
                    resp = Response(err.code, {'message': err.message})
                    print('!response!', json.dumps({'id': resp_id, 'code': resp.code, 'data': resp.data}), sep='')
                except Exception:
                    print('!response!', json.dumps({'id': resp_id, 'code': 500,
                                                    'data': {'message': "Internal Server Error"}}), sep='')
