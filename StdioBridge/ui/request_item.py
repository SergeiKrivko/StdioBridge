import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSizePolicy
from PyQtUIkit.core import KitFont
from PyQtUIkit.widgets import *
from qasync import asyncSlot

from StdioBridge._ui.expandable_widget import ExpandableWidget
from StdioBridge.client import Client


class Endpoint:
    def __init__(self, url: str, method: str, data: dict):
        self.url = url
        self.method = method
        self.body = data.get('body')
        self.path = data.get('path')
        self.query = data.get('query')


class ParameterItem(KitHBoxLayout):
    def __init__(self, name: str, param_type: str):
        super().__init__()
        self.spacing = 10
        left_layout = KitVBoxLayout()
        left_layout.spacing = 6
        self.addWidget(left_layout)

        left_layout.addWidget(label := KitLabel(name))
        label.font = 'bold'
        left_layout.addWidget(KitLabel(param_type))

        self._line_edit = KitLineEdit()
        self._line_edit.setFixedHeight(30)
        self.addWidget(self._line_edit)

    @property
    def value(self):
        return self._line_edit.text


class EndpointItem(ExpandableWidget):
    def __init__(self, client: Client, endpoint: Endpoint):
        super().__init__()
        self.client = client
        self.endpoint = endpoint
        self.path_params = dict()
        self.query_params = dict()

        self.top_layout.spacing = 10

        layout = KitHBoxLayout()
        layout.setFixedWidth(80)
        layout.main_palette = {
            'get': 'Menu',
            'post': 'Success',
            'put': 'Warning',
            'delete': 'Danger',
            'patch': 'Warning',
        }[endpoint.method]
        self.top_layout.addWidget(layout)

        method_label = KitLabel(endpoint.method.upper())
        method_label.font_size = KitFont.Size.BIG
        method_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(method_label)

        url_label = KitLabel(endpoint.url)
        self.top_layout.addWidget(url_label)

        self.body_layout.padding = 10
        self.body_layout.spacing = 6
        self.body_layout.alignment = Qt.AlignmentFlag.AlignTop
        self.body_layout.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if endpoint.path:
            self.body_layout.addWidget(label := KitLabel("Path parameters:"))
            label.font_size = KitFont.Size.BIG

            for key, item in self.endpoint.path.items():
                widget = ParameterItem(key, item)
                self.body_layout.addWidget(widget)
                self.path_params[key] = widget

        if endpoint.query:
            self.body_layout.addWidget(label := KitLabel("Query parameters:"))
            label.font_size = KitFont.Size.BIG

            for key, item in self.endpoint.query.items():
                widget = ParameterItem(key, item)
                self.body_layout.addWidget(widget)
                self.query_params[key] = widget

        if endpoint.body is not None:
            self.body_layout.addWidget(label := KitLabel("Request body:"))
            label.font_size = KitFont.Size.BIG

            self._body_edit = KitTextEdit()
            self._body_edit.setFixedHeight(200)
            self._body_edit.font = 'mono'
            self.body_layout.addWidget(self._body_edit)
        else:
            self._body_edit = None

        self.body_layout.addWidget(KitHSeparator())

        button = KitButton("Execute")
        button.font_size = KitFont.Size.BIG
        button.on_click = lambda: self.execute()
        self.body_layout.addWidget(button)

        self.body_layout.addWidget(KitHSeparator())

        layout = KitHBoxLayout()
        self.body_layout.addWidget(layout)
        layout.spacing = 6
        layout.addWidget(KitLabel("Code: "))
        self._code_label = KitLabel("?")
        self._code_label.font_size = KitFont.Size.BIG
        layout.addWidget(self._code_label, 100)

        self._response_body_widget = KitTextEdit()
        self._response_body_widget.font = 'mono'
        self._response_body_widget.setReadOnly(True)
        self._response_body_widget.setFixedHeight(200)
        self.body_layout.addWidget(self._response_body_widget)

    @asyncSlot()
    async def execute(self):
        url = self.endpoint.url
        for key, item in self.path_params.items():
            url = url.replace(f'{{{key}}}', item.value)
        i = 0
        for key, item in self.query_params.items():
            url += f"{'?' if i == 0 else '&'}{key}={item.value}"
            i += 1

        if isinstance(self._body_edit, KitTextEdit) and self._body_edit.toPlainText().strip():
            body = json.loads(self._body_edit.toPlainText())
        else:
            body = None
        resp = await self.client._request(self.endpoint.method, url, body, stream=True)
        self._code_label.text = str(resp.code)
        self._response_body_widget.setText('')
        text = ''
        async for el in resp:
            text += json.dumps(el, indent=2)
            text += '\n'
            self._response_body_widget.setText(text)
        self._code_label.text = str(resp.code)
