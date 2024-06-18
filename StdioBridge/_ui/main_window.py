import sys
from sys import argv

from PyQt6.QtCore import Qt
from PyQtUIkit.widgets import *
from qasync import asyncSlot

from StdioBridge._ui.request_item import Endpoint, EndpointItem
from StdioBridge._ui.search import search
from StdioBridge.client import Client


class MainWindow(KitMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)

        if len(argv) > 1:
            args = argv[1:]
        elif file := search():
            args = ['python' if sys.platform == 'win32' else 'python3', file]
        else:
            raise Exception("Api not found")
        self._client = Client(args, shell=True)

        main_layout = KitVBoxLayout()
        self.setCentralWidget(main_layout)

        scroll_area = KitScrollArea()
        main_layout.addWidget(scroll_area)

        self._scroll_layout = KitVBoxLayout()
        self._scroll_layout.alignment = Qt.AlignmentFlag.AlignTop
        self._scroll_layout.padding = 10
        self._scroll_layout.spacing = 10
        scroll_area.setWidget(self._scroll_layout)

    def showEvent(self, a0):
        super().showEvent(a0)
        self._load()

    @asyncSlot()
    async def _load(self):
        docs = await self._client.get('docs')
        docs = docs.data
        for key, items in docs.items():
            for method, item in items.items():
                endpoint = Endpoint(key, method, item)
                self._scroll_layout.addWidget(EndpointItem(self._client, endpoint))


def main():
    KitAsyncApplication(MainWindow).exec()


if __name__ == '__main__':
    main()
