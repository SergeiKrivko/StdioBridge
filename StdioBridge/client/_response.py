import asyncio


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


class StreamResponse:
    def __init__(self, dct: dict, lst: list):
        self._list = lst
        try:
            self._code = dct['code']
        except KeyError:
            self._code = 400
        self._finished = not self.ok
        self._captured = False

    @property
    def code(self) -> int:
        return self._code

    @property
    def ok(self) -> bool:
        return self._code < 400

    @property
    def finished(self) -> bool:
        return self._finished

    async def __aiter__(self):
        while not self._finished:
            while self._list:
                yield self._list.pop(0)
            await asyncio.sleep(0.2)
        while self._list:
            yield self._list.pop(0)

    def __str__(self):
        return f"<StreamResponse {self._code}>"
