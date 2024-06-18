from PyQtUIkit.widgets import *


class ExpandableWidget(KitVBoxLayout):
    def __init__(self):
        super().__init__()
        self.__expanded = False

        top_layout = KitLayoutButton()
        top_layout.spacing = 6
        top_layout.padding = 5
        top_layout.setFixedHeight(38)
        top_layout.on_click = self.__on_click
        self.addWidget(top_layout)

        self._top_layout = KitHBoxLayout()
        top_layout.addWidget(self._top_layout)

        self._icon_down = KitIconWidget('line-chevron-down')
        self._icon_down.setFixedSize(28, 28)
        top_layout.addWidget(self._icon_down)

        self._icon_up = KitIconWidget('line-chevron-up')
        self._icon_up.setFixedSize(28, 28)
        self._icon_up.hide()
        top_layout.addWidget(self._icon_up)

        self._body_layout = KitVBoxLayout()
        self._body_layout.hide()
        self.addWidget(self._body_layout)

    @property
    def top_layout(self):
        return self._top_layout

    @property
    def body_layout(self):
        return self._body_layout

    @property
    def expanded(self):
        return self.__expanded

    def __on_click(self):
        if self.__expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.__expanded = True
        self._icon_down.hide()
        self._icon_up.show()
        self._body_layout.show()

    def collapse(self):
        self.__expanded = False
        self._icon_up.hide()
        self._icon_down.show()
        self._body_layout.hide()


