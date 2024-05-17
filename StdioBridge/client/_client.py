import asyncio
import json
import subprocess
import threading
from uuid import uuid4


class Response:
    def __init__(self, dct: dict):
        try:
            self._code = dct['code']
            self._data = dct['data']
        except KeyError:
            self._code = 400
            self._data = {'message': 'Invalid Response'}

    @property
    def code(self) -> int:
        return self._code

    @property
    def data(self) -> dict:
        return self._data

    @property
    def ok(self) -> bool:
        return self._code < 400

    def __str__(self):
        return f"<Response {self._code}>"


class Client:
    def __init__(self, command: str | list[str], **kwargs) -> None:
        self._command = command
        self._kwargs = kwargs
        self._popen: subprocess.Popen | None = None
        self._responses: dict[str: dict] = dict()
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
            else:
                print(line)

    async def _request(self, method: str, url: str, data: dict):
        request_id = str(uuid4())
        self._popen.stdin.write(json.dumps({'id': request_id, 'method': method, 'url': url, 'data': data}) + '\n')
        self._popen.stdin.flush()
        while request_id not in self._responses:
            await asyncio.sleep(0.1)
        resp = self._responses[request_id]
        return Response(resp)

    async def get(self, url: str, data: dict = None) -> Response:
        resp = await self._request('get', url, data)
        return resp

    async def post(self, url: str, data: dict) -> Response:
        resp = await self._request('post', url, data)
        return resp

    async def put(self, url: str, data: dict) -> Response:
        resp = await self._request('put', url, data)
        return resp

    async def delete(self, url: str, data: dict = None) -> Response:
        resp = await self._request('delete', url, data)
        return resp

    async def patch(self, url: str, data: dict) -> Response:
        resp = await self._request('patch', url, data)
        return resp


async def main():
    client = Client('python -m TestPluginSrc.api')

    resp = await client.get('url?key=6')
    print(resp, resp.data)
    resp = await client.post('url/4d5515be-bf03-4c66-874e-31063045a9f6', {'1': 1, '2': 2, '5': 5})
    print(resp, resp.data)
    resp = await client.post('url/last', {'1': 1, '2': 2, '5': 5})
    print(resp, resp.data)
    client.terminate()


if __name__ == '__main__':
    asyncio.run(main())
