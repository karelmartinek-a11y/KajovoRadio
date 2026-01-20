from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class DrawerPanel(QtWidgets.QFrame):
    deleteClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)

        self.title = QtWidgets.QLabel('Detail')
        self.title.setStyleSheet('color: #E6E8EB; font-weight: 700; font-size: 14px;')

        self.body = QtWidgets.QTextEdit()
        self.body.setReadOnly(True)

        self.btn_delete = QtWidgets.QPushButton('Delete')
        self.btn_delete.setObjectName('Primary')

        v.addWidget(self.title)
        v.addWidget(self.body, 1)
        v.addWidget(self.btn_delete)

        self.btn_delete.clicked.connect(self.deleteClicked.emit)

    def set_content(self, title: str, text: str):
        self.title.setText(title)
        self.body.setPlainText(text)
