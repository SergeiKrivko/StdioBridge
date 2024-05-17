from inspect import isasyncgen

from StdioBridge.api.errors import ApiError


class Response:
    def __init__(self, code: int, data: dict):
        self.code = code
        self.data = data


class StreamResponse:
    def __init__(self, generator):
        self._generator = generator
        self.code = 200
        self.error = ''

    async def __aiter__(self):
        try:
            if isasyncgen(self._generator):
                async for item in self._generator:
                    yield item
            else:
                for item in self._generator:
                    yield item
        except ApiError as err:
            self.code = err.code
            self.error = err.message
        except Exception as err:
            self.code = 500
            self.error = f"{err.__class__.__name__}: {err}"
