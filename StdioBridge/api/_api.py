import asyncio
import json
from urllib.parse import urlparse, parse_qs

from aioconsole import ainput

from StdioBridge.api._response import Response, StreamResponse
from StdioBridge.api._router import Router
from StdioBridge.api.errors import *


class Api:
    def __init__(self):
        self._root_router = Router()

    def get(self, url: str):
        return self._root_router.get(url)

    def post(self, url: str):
        return self._root_router.post(url)

    def put(self, url: str):
        return self._root_router.put(url)

    def delete(self, url: str):
        return self._root_router.delete(url)

    def patch(self, url: str):
        return self._root_router.patch(url)

    def add_router(self, url: str, router: Router):
        self._root_router.add_router(url, router)

    async def _process_request(self, request: dict):
        resp_id = request.get('id')
        try:
            try:
                url = request['url']
                method = request['method']
                data = request['data']
                stream = request.get('stream', False)
            except KeyError:
                raise ErrorBadRequest("Missing 'url', 'method', or 'data' key")

            parsed_url = urlparse(url)
            query = parse_qs(parsed_url.query)
            url = parsed_url._replace(query="").geturl()

            func, path_params = self._root_router.found(url, method)
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
        except ApiError as err:
            resp = Response(err.code, {'message': err.message})
            print('!response!', json.dumps({'id': resp_id, 'code': resp.code, 'data': resp.data}), sep='')
        except Exception:
            print('!response!', json.dumps({'id': resp_id, 'code': 500,
                                            'data': {'message': "Internal Server Error"}}), sep='')

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        while True:
            try:
                inp = await ainput()
                data = json.loads(inp)
            except json.JSONDecodeError:
                print("Invalid JSON")
            else:
                asyncio.create_task(self._process_request(data)).done()
