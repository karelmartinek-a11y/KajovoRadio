from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.ui.widgets.eye_indicator import EyeIndicator


class FooterBar(QtWidgets.QFrame):
    playClicked = QtCore.Signal()
    stopClicked = QtCore.Signal()
    muteToggled = QtCore.Signal(bool)
    volumeChanged = QtCore.Signal(float)
    boostToggled = QtCore.Signal(bool)
    hotkeyPressed = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('FooterBar')

        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)

        self.btn_play = QtWidgets.QPushButton('PLAY')
        self.btn_stop = QtWidgets.QPushButton('STOP')
        self.btn_mute = QtWidgets.QPushButton('MUTE')

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(80)

        self.lbl_vol = QtWidgets.QLabel('80%')
        self.lbl_mono = QtWidgets.QLabel('MONO (L=R)')

        self.chk_boost = QtWidgets.QCheckBox('BOOST')

        self.eye = EyeIndicator()

        h.addWidget(self.btn_play)
        h.addWidget(self.btn_stop)
        h.addWidget(self.btn_mute)
        h.addSpacing(8)

        h.addWidget(QtWidgets.QLabel('Hlasitost'))
        h.addWidget(self.slider, 1)
        h.addWidget(self.lbl_vol)
        h.addSpacing(8)
        h.addWidget(self.lbl_mono)
        h.addWidget(self.chk_boost)
        h.addWidget(self.eye)

        h.addSpacing(10)

        self.hotkeys = []
        for i in range(8):
            b = QtWidgets.QPushButton(f'H{i+1}')
            b.setMinimumWidth(60)
            b.clicked.connect(lambda _=False, ix=i: self.hotkeyPressed.emit(ix))
            self.hotkeys.append(b)
            h.addWidget(b)

        self.btn_play.clicked.connect(self.playClicked.emit)
        self.btn_stop.clicked.connect(self.stopClicked.emit)
        self.btn_mute.clicked.connect(lambda: self.muteToggled.emit(True))
        self.slider.valueChanged.connect(self._vol)
        self.chk_boost.toggled.connect(self.boostToggled.emit)

    def _vol(self, v: int):
        self.lbl_vol.setText(f'{v}%')
        self.volumeChanged.emit(v / 100.0)

    def set_hotkey_labels(self, labels: list[str]):
        for i, b in enumerate(self.hotkeys):
            if i < len(labels) and labels[i]:
                b.setText(labels[i])
            else:
                b.setText(f'H{i+1}')
