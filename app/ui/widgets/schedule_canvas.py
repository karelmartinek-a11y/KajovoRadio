from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Callable

from PySide6 import QtCore, QtGui, QtWidgets


DAY_NAMES = ['Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne']


@dataclass
class CanvasConfig:
    columns: bool = True  # True=7 columns, False=7 rows
    zoom_minutes_per_grid: int = 10


class ScheduleCanvas(QtWidgets.QWidget):
    """Week plan 'canvas'.

    This is a deliberately lightweight custom widget that supports:
    - rendering time grid (00:00-24:00)
    - drag&drop 'pin event' at HH:MM
    - draw stream blocks by mouse drag with snap-to-grid (primary interaction; no modifier)

    It emits high-level signals; MainWindow updates state + drawer.
    """

    eventDropped = QtCore.Signal(int, str, str, str)  # day_index, hhmm, item_type, ref_id
    streamBlockDrawn = QtCore.Signal(int, str, str)   # day_index, start_hhmm, end_hhmm
    blockClicked = QtCore.Signal(str, str)            # block_kind ('event'/'stream'), block_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.config = CanvasConfig()

        self._now_dt = QtCore.QDateTime.currentDateTime()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

        self._events = []  # list of dict for paint
        self._streams = []

        # drawing state
        self._drawing = False
        self._draw_day = 0
        self._draw_start_min = 0
        self._draw_end_min = 0

    def set_data(self, events: list[dict], streams: list[dict]):
        self._events = events
        self._streams = streams
        self.update()

    def set_columns_mode(self, columns: bool):
        self.config.columns = bool(columns)
        self.update()

    def set_zoom(self, minutes_grid: int):
        self.config.zoom_minutes_per_grid = int(minutes_grid)
        self.update()

    def _tick(self):
        self._now_dt = QtCore.QDateTime.currentDateTime()
        self.update()

    # Geometry helpers
    def _snap_min(self, minute_of_day: int) -> int:
        g = max(5, int(self.config.zoom_minutes_per_grid))
        return int(round(minute_of_day / g) * g)

    def _minute_to_y(self, minute_of_day: int, rect: QtCore.QRect) -> int:
        return rect.top() + int((minute_of_day / (24*60)) * rect.height())

    def _y_to_minute(self, y: int, rect: QtCore.QRect) -> int:
        rel = max(0, min(rect.height(), y - rect.top()))
        return int((rel / rect.height()) * (24*60))

    def _day_rects(self) -> list[QtCore.QRect]:
        r = self.rect().adjusted(14, 30, -14, -14)
        rects = []
        if self.config.columns:
            w = r.width() // 7
            for i in range(7):
                rects.append(QtCore.QRect(r.left() + i*w, r.top(), w, r.height()))
        else:
            h = r.height() // 7
            for i in range(7):
                rects.append(QtCore.QRect(r.left(), r.top() + i*h, r.width(), h))
        return rects

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        bg = QtGui.QColor('#0B0D10')
        panel = QtGui.QColor('#0F1217')
        grid = QtGui.QColor('#111824')
        line = QtGui.QColor('#1A2230')
        cyan = QtGui.QColor('#2EE6FF')
        yellow = QtGui.QColor('#F4C61C')
        grey = QtGui.QColor('#C8CDD3')

        p.fillRect(self.rect(), bg)

        # Title / controls hint
        p.setPen(grey)
        p.setFont(QtGui.QFont('Segoe UI', 10, 700))
        p.drawText(14, 20, 'Plán týdne (drag & drop / draw)')

        day_rects = self._day_rects()

        # Draw day headers and background
        p.setFont(QtGui.QFont('Segoe UI', 9, 700))
        for i, dr in enumerate(day_rects):
            p.setPen(line)
            p.setBrush(panel)
            p.drawRoundedRect(dr.adjusted(2, 2, -2, -2), 10, 10)
            p.setPen(grey)
            p.drawText(dr.adjusted(10, 8, -10, -8), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, DAY_NAMES[i])

        # Grid lines (hour)
        p.setPen(QtGui.QPen(grid, 1))
        for h in range(0, 25):
            minute = h * 60
            for dr in day_rects:
                y = self._minute_to_y(minute, dr)
                p.drawLine(dr.left()+6, y, dr.right()-6, y)

        # Default playlist background hint
        p.setPen(QtCore.Qt.NoPen)
        playlist_col = QtGui.QColor('#132636')
        playlist_col.setAlpha(50)
        for dr in day_rects:
            p.setBrush(playlist_col)
            p.drawRoundedRect(dr.adjusted(6, 26, -6, -6), 8, 8)

        # Stream blocks
        for b in self._streams:
            day = int(b['day_index'])
            if day < 0 or day > 6:
                continue
            dr = day_rects[day].adjusted(8, 30, -8, -8)
            y0 = self._minute_to_y(b['start_min'], dr)
            y1 = self._minute_to_y(b['end_min'], dr)
            rr = QtCore.QRect(dr.left(), min(y0, y1), dr.width(), max(22, abs(y1-y0)))
            col = QtGui.QColor('#2EE6FF')
            col.setAlpha(70)
            p.setBrush(col)
            p.setPen(QtGui.QPen(cyan, 1))
            p.drawRoundedRect(rr, 8, 8)
            p.setPen(grey)
            p.setFont(QtGui.QFont('Segoe UI', 8, 700))
            p.drawText(rr.adjusted(8, 6, -8, -6), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, 'STREAM')

        # Pin events (track/hláška)
        for e in self._events:
            day = int(e['day_index'])
            if day < 0 or day > 6:
                continue
            dr = day_rects[day].adjusted(8, 30, -8, -8)
            y = self._minute_to_y(e['minute'], dr)
            rr = QtCore.QRect(dr.left(), y-10, dr.width(), 20)
            p.setBrush(QtGui.QColor('#F4C61C33'))
            p.setPen(QtGui.QPen(yellow, 1))
            p.drawRoundedRect(rr, 8, 8)
            p.setPen(grey)
            p.setFont(QtGui.QFont('Segoe UI', 8, 700))
            p.drawText(rr.adjusted(8, 0, -8, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, e.get('label', 'EVENT'))

        # Now marker
        now = self._now_dt
        # Qt day: 1=Mon..7=Sun
        di = max(0, min(6, now.date().dayOfWeek() - 1))
        minute_now = now.time().hour() * 60 + now.time().minute()
        dr = day_rects[di].adjusted(8, 30, -8, -8)
        y = self._minute_to_y(minute_now, dr)
        p.setPen(QtGui.QPen(cyan, 2))
        p.drawLine(dr.left(), y, dr.right(), y)
        p.setPen(cyan)
        p.setFont(QtGui.QFont('Segoe UI', 8, 700))
        p.drawText(dr.right()-60, y-14, 56, 14, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, 'Now')

        # Draw in-progress stream block while drawing
        if self._drawing:
            dr = day_rects[self._draw_day].adjusted(8, 30, -8, -8)
            y0 = self._minute_to_y(self._draw_start_min, dr)
            y1 = self._minute_to_y(self._draw_end_min, dr)
            rr = QtCore.QRect(dr.left(), min(y0, y1), dr.width(), max(22, abs(y1-y0)))
            p.setBrush(QtGui.QColor('#2EE6FF22'))
            p.setPen(QtGui.QPen(cyan, 1, QtCore.Qt.DashLine))
            p.drawRoundedRect(rr, 8, 8)

    def _pos_to_day_and_minute(self, pos: QtCore.QPoint) -> Optional[tuple[int, int, QtCore.QRect]]:
        rects = self._day_rects()
        for i, r in enumerate(rects):
            rr = r.adjusted(8, 30, -8, -8)
            if rr.contains(pos):
                minute = self._y_to_minute(pos.y(), rr)
                minute = self._snap_min(minute)
                return i, minute, rr
        return None

    # Drag & drop pins
    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasFormat('application/x-rkj-item'):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        info = self._pos_to_day_and_minute(e.position().toPoint())
        if not info:
            return
        day, minute, _ = info
        md = e.mimeData().data('application/x-rkj-item').data().decode('utf-8')
        # payload: item_type|ref_id|label
        parts = md.split('|')
        if len(parts) >= 2:
            item_type, ref_id = parts[0], parts[1]
            hhmm = f"{minute//60:02d}:{minute%60:02d}"
            self.eventDropped.emit(day, hhmm, item_type, ref_id)
        e.acceptProposedAction()

    # Draw stream blocks
    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        # Stream draw is the primary interaction as per spec; do not require Shift.
        if e.button() == QtCore.Qt.LeftButton:
            info = self._pos_to_day_and_minute(e.position().toPoint())
            if info:
                day, minute, _ = info
                self._drawing = True
                self._draw_day = day
                self._draw_start_min = minute
                self._draw_end_min = minute
                self.update()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._drawing:
            info = self._pos_to_day_and_minute(e.position().toPoint())
            if info:
                _, minute, _ = info
                self._draw_end_min = minute
                self.update()
                return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._drawing and e.button() == QtCore.Qt.LeftButton:
            self._drawing = False
            s = min(self._draw_start_min, self._draw_end_min)
            t = max(self._draw_start_min, self._draw_end_min)
            # Minimum 10 minutes block
            if t - s < 10:
                t = s + 10
            start = f"{s//60:02d}:{s%60:02d}"
            end = f"{t//60:02d}:{t%60:02d}"
            self.streamBlockDrawn.emit(self._draw_day, start, end)
            self.update()
            return
        super().mouseReleaseEvent(e)
