from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class AudioFileTab(QtWidgets.QWidget):
    importFilesClicked = QtCore.Signal()
    scanFolderClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        self.btn_import = QtWidgets.QPushButton('Přidat audio soubory…')
        self.btn_scan = QtWidgets.QPushButton('Prohledat adresář…')
        row.addWidget(self.btn_import)
        row.addWidget(self.btn_scan)
        row.addStretch(1)

        self.list = QtWidgets.QListWidget()
        self.search = QtWidgets.QLineEdit(); self.search.setPlaceholderText('Fulltextové vyhledávání…')

        v.addLayout(row)
        v.addWidget(self.search)
        v.addWidget(self.list, 1)

        self.btn_import.clicked.connect(self.importFilesClicked.emit)
        self.btn_scan.clicked.connect(self.scanFolderClicked.emit)


class SpotifyTab(QtWidgets.QWidget):
    searchClicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        self.q = QtWidgets.QLineEdit(); self.q.setPlaceholderText('Vyhledat track na Spotify…')
        self.btn = QtWidgets.QPushButton('Hledat')
        row.addWidget(self.q, 1)
        row.addWidget(self.btn)

        self.list = QtWidgets.QListWidget()
        v.addLayout(row)
        v.addWidget(self.list, 1)

        self.btn.clicked.connect(lambda: self.searchClicked.emit(self.q.text().strip()))


class DynamicTextsTab(QtWidgets.QWidget):
    createClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)

        self.btn_create = QtWidgets.QPushButton('Nová hláška')
        self.btn_create.setObjectName('Primary')
        self.list = QtWidgets.QListWidget()
        v.addWidget(self.btn_create)
        v.addWidget(self.list, 1)

        self.btn_create.clicked.connect(self.createClicked.emit)


class StreamsTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)

        self.search = QtWidgets.QLineEdit(); self.search.setPlaceholderText('Vyhledávání streamů (externí db)…')
        self.list = QtWidgets.QListWidget()
        v.addWidget(self.search)
        v.addWidget(self.list, 1)


class SettingsTab(QtWidgets.QWidget):
    settingsChanged = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        f = QtWidgets.QFormLayout(self)
        f.setContentsMargins(14, 14, 14, 14)
        f.setSpacing(10)

        self.spotify_key = QtWidgets.QLineEdit(); self.spotify_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.openai_key = QtWidgets.QLineEdit(); self.openai_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.azure_key = QtWidgets.QLineEdit(); self.azure_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.azure_region = QtWidgets.QLineEdit()

        f.addRow('Spotify API-KEY', self.spotify_key)
        f.addRow('OpenAI API-KEY', self.openai_key)
        f.addRow('Azure TTS KEY', self.azure_key)
        f.addRow('Azure TTS REGION', self.azure_region)

        self.spotify_key.textChanged.connect(self._emit)
        self.openai_key.textChanged.connect(self._emit)
        self.azure_key.textChanged.connect(self._emit)
        self.azure_region.textChanged.connect(self._emit)

    def set_values(self, d: dict):
        self.spotify_key.setText(d.get('spotify_api_key',''))
        self.openai_key.setText(d.get('openai_api_key',''))
        self.azure_key.setText(d.get('azure_tts_key',''))
        self.azure_region.setText(d.get('azure_tts_region',''))

    def _emit(self):
        self.settingsChanged.emit({
            'spotify_api_key': self.spotify_key.text(),
            'openai_api_key': self.openai_key.text(),
            'azure_tts_key': self.azure_key.text(),
            'azure_tts_region': self.azure_region.text(),
        })
