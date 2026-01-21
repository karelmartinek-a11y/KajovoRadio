from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.ui.widgets.schedule_canvas import ScheduleCanvas


class SchedulePanel(QtWidgets.QFrame):
    """Right-side schedule area with inline controls (no heavy dialogs).

    - 7 sloupců / 7 řádků
    - Zoom timeline: 1h / 30m / 15m (scrollable canvas)
    - Snap: 5 / 10 / 15 minut (default 10)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SchedulePanel")

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(10)

        # Toolbar
        tb = QtWidgets.QFrame()
        tb.setObjectName("ScheduleToolbar")
        th = QtWidgets.QHBoxLayout(tb)
        th.setContentsMargins(10, 10, 10, 10)
        th.setSpacing(10)

        self.btn_cols = QtWidgets.QToolButton()
        self.btn_cols.setText("7 sloupců")
        self.btn_cols.setCheckable(True)
        self.btn_cols.setChecked(True)

        self.btn_rows = QtWidgets.QToolButton()
        self.btn_rows.setText("7 řádků")
        self.btn_rows.setCheckable(True)

        # keep as a simple "segmented" behavior
        grp = QtWidgets.QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.btn_cols, 1)
        grp.addButton(self.btn_rows, 2)

        th.addWidget(QtWidgets.QLabel("Zobrazení:"))
        th.addWidget(self.btn_cols)
        th.addWidget(self.btn_rows)
        th.addSpacing(12)

        self.cmb_zoom = QtWidgets.QComboBox()
        self.cmb_zoom.addItems(["1h", "30m", "15m"])
        self.cmb_zoom.setCurrentText("30m")
        th.addWidget(QtWidgets.QLabel("Zoom:"))
        th.addWidget(self.cmb_zoom)
        th.addSpacing(12)

        self.cmb_snap = QtWidgets.QComboBox()
        self.cmb_snap.addItems(["5m", "10m", "15m"])
        self.cmb_snap.setCurrentText("10m")
        th.addWidget(QtWidgets.QLabel("Snap:"))
        th.addWidget(self.cmb_snap)
        th.addStretch(1)

        # Canvas in scroll area
        self.canvas = ScheduleCanvas()
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setWidget(self.canvas)

        v.addWidget(tb)
        v.addWidget(self.scroll, 1)

        # Wiring
        self.btn_cols.toggled.connect(lambda on: self.canvas.set_columns_mode(bool(on)))
        self.btn_rows.toggled.connect(lambda on: self.canvas.set_columns_mode(not bool(on)))
        self.cmb_zoom.currentTextChanged.connect(self._apply_zoom)
        self.cmb_snap.currentTextChanged.connect(self._apply_snap)

        # defaults
        self._apply_zoom(self.cmb_zoom.currentText())
        self._apply_snap(self.cmb_snap.currentText())

    def _apply_zoom(self, s: str) -> None:
        # Larger px/hour => more vertical space => easier drawing/catching.
        mapping = {"1h": 60, "30m": 120, "15m": 240}
        self.canvas.set_view_zoom(mapping.get(s, 120))

    def _apply_snap(self, s: str) -> None:
        mapping = {"5m": 5, "10m": 10, "15m": 15}
        self.canvas.set_snap_minutes(mapping.get(s, 10))
