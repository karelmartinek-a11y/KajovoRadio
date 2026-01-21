from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


DAY_NAMES = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]


class _BasePopover(QtWidgets.QFrame):
    rejected = QtCore.Signal()

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.setObjectName("PopoverFrame")
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)

        self.lbl_title = QtWidgets.QLabel(title)
        self.lbl_title.setObjectName("PopoverTitle")
        v.addWidget(self.lbl_title)

        if subtitle:
            self.lbl_subtitle = QtWidgets.QLabel(subtitle)
            self.lbl_subtitle.setObjectName("PopoverSubtitle")
            self.lbl_subtitle.setWordWrap(True)
            v.addWidget(self.lbl_subtitle)
        else:
            self.lbl_subtitle = None

    def show_at(self, global_pos: QtCore.QPoint) -> None:
        self.adjustSize()
        # keep on-screen as much as possible
        screen = QtGui.QGuiApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1280, 720)
        x = max(geo.left() + 10, min(global_pos.x(), geo.right() - self.width() - 10))
        y = max(geo.top() + 10, min(global_pos.y(), geo.bottom() - self.height() - 10))
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Escape:
            self.rejected.emit()
            self.close()
            return
        super().keyPressEvent(e)


class SchedulePopover(_BasePopover):
    """Popover shown after dropping an item onto the schedule.

    Allows selecting days (presets) and adjusting the HH:MM time inline.
    """

    acceptedDaysTime = QtCore.Signal(list, str)  # days[int], hhmm[str]

    def __init__(self, title: str, subtitle: str, initial_day_index: int, initial_hhmm: str, parent=None):
        super().__init__(title=title, subtitle=subtitle, parent=parent)

        v = self.layout()

        # Day presets
        presets = QtWidgets.QHBoxLayout()
        self.btn_only = QtWidgets.QToolButton(); self.btn_only.setText("Jen tento den")
        self.btn_wd = QtWidgets.QToolButton(); self.btn_wd.setText("Všední dny")
        self.btn_we = QtWidgets.QToolButton(); self.btn_we.setText("Víkend")
        self.btn_all = QtWidgets.QToolButton(); self.btn_all.setText("Každý den")
        for b in (self.btn_only, self.btn_wd, self.btn_we, self.btn_all):
            b.setAutoRaise(False)
        presets.addWidget(self.btn_only)
        presets.addWidget(self.btn_wd)
        presets.addWidget(self.btn_we)
        presets.addWidget(self.btn_all)
        presets.addStretch(1)
        v.addItem(presets)

        # Day toggles
        days = QtWidgets.QHBoxLayout()
        self.day_btns: list[QtWidgets.QToolButton] = []
        for i, dn in enumerate(DAY_NAMES):
            b = QtWidgets.QToolButton()
            b.setText(dn)
            b.setCheckable(True)
            if i == int(initial_day_index):
                b.setChecked(True)
            self.day_btns.append(b)
            days.addWidget(b)
        days.addStretch(1)
        v.addItem(days)

        # Time row
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Čas:"))
        self.time = QtWidgets.QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        hh, mm = 0, 0
        try:
            hh, mm = map(int, initial_hhmm.split(":"))
        except Exception:
            pass
        self.time.setTime(QtCore.QTime(hh, mm))
        row.addWidget(self.time)
        row.addStretch(1)
        v.addItem(row)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QtWidgets.QPushButton("Zrušit")
        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_ok.setObjectName("Primary")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        v.addItem(btns)

        # Wiring presets
        self.btn_only.clicked.connect(lambda: self._set_days([int(initial_day_index)]))
        self.btn_wd.clicked.connect(lambda: self._set_days([0, 1, 2, 3, 4]))
        self.btn_we.clicked.connect(lambda: self._set_days([5, 6]))
        self.btn_all.clicked.connect(lambda: self._set_days([0, 1, 2, 3, 4, 5, 6]))

        self.btn_cancel.clicked.connect(self._reject)
        self.btn_ok.clicked.connect(self._accept)

    def _set_days(self, idxs: list[int]) -> None:
        for i, b in enumerate(self.day_btns):
            b.setChecked(i in idxs)

    def _accept(self) -> None:
        days = [i for i, b in enumerate(self.day_btns) if b.isChecked()]
        if not days:
            days = [0]
        t = self.time.time()
        hhmm = f"{t.hour():02d}:{t.minute():02d}"
        self.acceptedDaysTime.emit(days, hhmm)
        self.close()

    def _reject(self) -> None:
        self.rejected.emit()
        self.close()


class StreamSelectPopover(_BasePopover):
    """Popover shown after drawing a stream block.

    Offers quick search + selection from the internal streams DB.
    """

    acceptedStream = QtCore.Signal(str)  # stream_id

    def __init__(self, title: str, subtitle: str, streams: list[tuple[str, str]], parent=None):
        super().__init__(title=title, subtitle=subtitle, parent=parent)
        v = self.layout()

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Vyhledat stream…")
        v.addWidget(self.search)

        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        v.addWidget(self.list)

        self._all = list(streams)
        self._fill("")

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QtWidgets.QPushButton("Zrušit")
        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_ok.setObjectName("Primary")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        v.addItem(btns)

        self.search.textChanged.connect(self._fill)
        self.btn_cancel.clicked.connect(self._reject)
        self.btn_ok.clicked.connect(self._accept)
        self.list.itemDoubleClicked.connect(lambda *_: self._accept())

    def _fill(self, q: str) -> None:
        q = (q or "").strip().lower()
        self.list.clear()
        for sid, name in self._all:
            if q and q not in name.lower():
                continue
            it = QtWidgets.QListWidgetItem(name)
            it.setData(QtCore.Qt.UserRole + 1, sid)
            self.list.addItem(it)
        if self.list.count() > 0 and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)

    def _accept(self) -> None:
        it = self.list.currentItem()
        if not it:
            self._reject()
            return
        sid = it.data(QtCore.Qt.UserRole + 1)
        if not sid:
            self._reject()
            return
        self.acceptedStream.emit(str(sid))
        self.close()

    def _reject(self) -> None:
        self.rejected.emit()
        self.close()
