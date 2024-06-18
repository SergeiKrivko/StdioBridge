from types import GenericAlias


class MethodDocs:
    def __init__(self, method: str, url: str, annotations: dict):
        self.method = method
        self.url = url
        self.path_params = dict()
        self.query_params = dict()
        self.request_body = None

        for el in url.split('{')[1:]:
            if el.count('}') != 1:
                raise ValueError("Invalid url format")
            el = el.split('}')[0]
            self.path_params[el] = str(annotations.get(el, '?'))

        for key, item in annotations.items():
            if key in self.path_params:
                continue
            if item == dict or isinstance(item, GenericAlias) and item.__origin__ == dict:
                self.request_body = 'Any'
            else:
                try:
                    import pydantic
                    if issubclass(item, pydantic.BaseModel):
                        self.request_body = str(item)
                    else:
                        self.query_params[key] = str(item)
                except ImportError:
                    self.query_params[key] = str(item)

    def dict(self):
        return {
            'path': self.path_params,
            'query': self.query_params,
            'body': self.request_body,
        }

