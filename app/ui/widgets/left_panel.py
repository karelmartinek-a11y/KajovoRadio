from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6 import QtCore, QtGui, QtWidgets


def make_item_mime(item_type: str, ref_id: str, label: str) -> QtCore.QMimeData:
    md = QtCore.QMimeData()
    payload = f"{item_type}|{ref_id}|{label}".encode('utf-8')
    md.setData('application/x-rkj-item', payload)
    return md


class DraggableListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def startDrag(self, supportedActions):
        it = self.currentItem()
        if not it:
            return
        item_type = it.data(QtCore.Qt.UserRole + 1)
        ref_id = it.data(QtCore.Qt.UserRole + 2)
        label = it.text()

        drag = QtGui.QDrag(self)
        drag.setMimeData(make_item_mime(item_type, ref_id, label))
        drag.exec(QtCore.Qt.CopyAction)


class LeftPanel(QtWidgets.QFrame):
    addToPlaylistRequested = QtCore.Signal(str, str)  # item_type, ref_id
    infoRequested = QtCore.Signal(str, str)
    deleteRequested = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('LeftPanel')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.box_tracks = self._make_box('Tracky (AudioFile + Spotify)')
        self.box_spotify = self._make_box('Spotify vyhledávání')
        self.box_texts = self._make_box('Dynamické texty')
        self.box_playlist = self._make_box('Aktuální playlist (loop)')

        layout.addWidget(self.box_tracks['box'])
        layout.addWidget(self.box_spotify['box'])
        layout.addWidget(self.box_texts['box'])
        layout.addWidget(self.box_playlist['box'])
        layout.addStretch(1)

        self._wire_box_actions(self.box_tracks)
        self._wire_box_actions(self.box_spotify)
        self._wire_box_actions(self.box_texts)
        self._wire_box_actions(self.box_playlist)

        # Playlist specifics
        self.box_playlist['list'].setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.box_playlist['progress'] = QtWidgets.QProgressBar()
        self.box_playlist['progress'].setRange(0, 50)
        self.box_playlist['progress'].setValue(0)
        self.box_playlist['box'].layout().addWidget(self.box_playlist['progress'])

    def _make_box(self, title: str) -> dict:
        box = QtWidgets.QGroupBox(title)
        v = QtWidgets.QVBoxLayout(box)
        v.setSpacing(8)

        search = QtWidgets.QLineEdit()
        search.setPlaceholderText('Vyhledávání (fulltext)…')

        lst = DraggableListWidget()

        actions = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QToolButton(); btn_add.setText('+ do playlistu')
        btn_info = QtWidgets.QToolButton(); btn_info.setText('Info')
        btn_del = QtWidgets.QToolButton(); btn_del.setText('Smazat')
        actions.addWidget(btn_add)
        actions.addWidget(btn_info)
        actions.addWidget(btn_del)
        actions.addStretch(1)

        v.addWidget(search)
        v.addWidget(lst, 1)
        v.addLayout(actions)

        return {'box': box, 'search': search, 'list': lst, 'btn_add': btn_add, 'btn_info': btn_info, 'btn_del': btn_del}

    def _wire_box_actions(self, b: dict) -> None:
        b['btn_add'].clicked.connect(lambda: self._emit_for_current(b, 'add'))
        b['btn_info'].clicked.connect(lambda: self._emit_for_current(b, 'info'))
        b['btn_del'].clicked.connect(lambda: self._emit_for_current(b, 'del'))

    def _emit_for_current(self, b: dict, action: str) -> None:
        it = b['list'].currentItem()
        if not it:
            return
        item_type = it.data(QtCore.Qt.UserRole + 1)
        ref_id = it.data(QtCore.Qt.UserRole + 2)
        if action == 'add':
            self.addToPlaylistRequested.emit(item_type, ref_id)
        elif action == 'info':
            self.infoRequested.emit(item_type, ref_id)
        elif action == 'del':
            self.deleteRequested.emit(item_type, ref_id)

    def set_tracks(self, items: list[tuple[str, str, str]]):
        # (ref_id, label, sourceType)
        self._fill_list(self.box_tracks['list'], [(sid, label, stype) for sid, label, stype in items])

    def set_spotify_search_results(self, items: list[tuple[str, str]]):
        # (ref_id, label)
        self._fill_list(self.box_spotify['list'], [(rid, label, 'spotify') for rid, label in items])

    def set_dynamic_texts(self, items: list[tuple[str, str]]):
        self._fill_list(self.box_texts['list'], [(rid, label, 'dynamic_text') for rid, label in items])

    def set_playlist(self, items: list[tuple[str, str, str]]):
        # (item_type, ref_id, label)
        lst = self.box_playlist['list']
        lst.clear()
        for item_type, ref_id, label in items:
            it = QtWidgets.QListWidgetItem(label)
            it.setData(QtCore.Qt.UserRole + 1, item_type)
            it.setData(QtCore.Qt.UserRole + 2, ref_id)
            lst.addItem(it)
        # progress
        self.box_playlist['progress'].setValue(len(items))

    @staticmethod
    def _fill_list(lst: QtWidgets.QListWidget, items: list[tuple[str, str, str]]):
        lst.clear()
        for ref_id, label, item_type in items:
            it = QtWidgets.QListWidgetItem(label)
            it.setData(QtCore.Qt.UserRole + 1, item_type)
            it.setData(QtCore.Qt.UserRole + 2, ref_id)
            lst.addItem(it)
