import asyncio
import json
import subprocess
import threading
from uuid import uuid4

from StdioBridge.client._response import Response, StreamResponse


class Client:
    def __init__(self, command: str | list[str], **kwargs) -> None:
        self._command = command
        self._kwargs = kwargs
        self._popen: subprocess.Popen | None = None
        self._responses: dict[str: dict] = dict()
        self._streams: dict[str: list[dict]] = dict()
        self._stream_responses: dict[str: StreamResponse] = dict()
        self._thread: threading.Thread | None = None
        self._run()

    def _run(self) -> None:
        self._popen = subprocess.Popen(self._command,
                                       text=True,
                                       encoding='utf-8',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       **self._kwargs)
        threading.Thread(target=self._read_stdout, daemon=True).start()

    def terminate(self):
        self._popen.stdin.close()

    def _read_stdout(self):
        for line in iter(self._popen.stdout.readline, ''):
            if self._popen.stdin.closed:
                break
            elif line.startswith('!response!'):
                dct = json.loads(line[len('!response!'):])
                self._responses[dct['id']] = dct
            elif line.startswith('!stream_start!'):
                dct = json.loads(line[len('!stream_start!'):])
                self._streams[dct['id']] = lst = []
                self._stream_responses[dct['id']] = StreamResponse(dct, lst)
            elif line.startswith('!stream_chunk!'):
                dct = json.loads(line[len('!stream_chunk!'):])
                self._streams[dct['id']].append(dct['chunk'])
            elif line.startswith('!stream_end!'):
                dct = json.loads(line[len('!stream_end!'):])
                self._streams.pop(dct['id'])
                resp = self._stream_responses[dct['id']]
                resp._finished = True
                resp._code = dct['code']
                if resp._captured:
                    self._stream_responses.pop(dct['id'])
            else:
                print(line, end='')

    async def _request(self, method: str, url: str, data: dict, stream=False) -> Response | StreamResponse:
        request_id = str(uuid4())
        self._popen.stdin.write(json.dumps({'id': request_id, 'method': method, 'url': url,
                                            'data': data, 'stream': stream}) + '\n')
        self._popen.stdin.flush()

        if stream:
            while request_id not in self._stream_responses:
                await asyncio.sleep(0.2)
            resp = self._stream_responses[request_id]
            resp._captured = True
            if resp.finished:
                self._stream_responses.pop(request_id)
            return resp

        while request_id not in self._responses:
            await asyncio.sleep(0.2)
        resp = self._responses[request_id]
        return Response(resp)

    async def get(self, url: str, data: dict = None, stream=False) -> Response | StreamResponse:
        resp = await self._request('get', url, data, stream)
        return resp

    async def post(self, url: str, data: dict, stream=False) -> Response | StreamResponse:
        resp = await self._request('post', url, data, stream)
        return resp

    async def put(self, url: str, data: dict, stream=False) -> Response | StreamResponse:
        resp = await self._request('put', url, data, stream)
        return resp

    async def delete(self, url: str, data: dict = None, stream=False) -> Response | StreamResponse:
        resp = await self._request('delete', url, data, stream)
        return resp

    async def patch(self, url: str, data: dict, stream=False) -> Response | StreamResponse:
        resp = await self._request('patch', url, data, stream)
        return resp
