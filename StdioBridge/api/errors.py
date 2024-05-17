class ApiError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code}: {self.message}'


class ErrorBadRequest(ApiError):
    def __init__(self, message: str = 'Bad Request'):
        super().__init__(400, message)


class ErrorUnauthorized(ApiError):
    def __init__(self, message: str = 'Unauthorized'):
        super().__init__(401, message)


class ErrorForbidden(ApiError):
    def __init__(self, message: str = 'Forbidden'):
        super().__init__(403, message)


class ErrorNotFound(ApiError):
    def __init__(self, message: str = 'Not Found'):
        super().__init__(404, message)


class ErrorMethodNotAllowed(ApiError):
    def __init__(self, message: str = 'Method Not Allowed'):
        super().__init__(405, message)


class ErrorNotAcceptable(ApiError):
    def __init__(self, message: str = 'Not Acceptable'):
        super().__init__(406, message)


class ErrorUnsupportedMediaType(ApiError):
    def __init__(self, message: str = 'Unsupported Media Type'):
        super().__init__(415, message)


class ErrorUnprocessableEntity(ApiError):
    def __init__(self, message: str = 'Unprocessable Entity'):
        super().__init__(422, message)


class InternalServerError(ApiError):
    def __init__(self, message: str = 'Internal Server Error'):
        super().__init__(500, message)


