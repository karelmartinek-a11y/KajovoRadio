from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class EyeIndicator(QtWidgets.QWidget):
    """Animated 'eye' indicator driven by RMS/peak values.

    - iris pulse ~ RMS
    - eyelid openness ~ peak
    - color shifts: grey -> cyan, and yellow accent when BOOST ON
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 34)
        self._rms = 0.0
        self._peak = 0.0
        self._muted = False
        self._stopped = True
        self._boost = False
        self._phase = 0.0

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

    def set_state(self, rms: float, peak: float, muted: bool, stopped: bool, boost: bool) -> None:
        self._rms = max(0.0, min(1.0, float(rms)))
        self._peak = max(0.0, min(1.0, float(peak)))
        self._muted = bool(muted)
        self._stopped = bool(stopped)
        self._boost = bool(boost)

    def _tick(self):
        # Minimal animation when stopped
        speed = 0.6 if self._stopped else 2.2
        self._phase = (self._phase + 0.016 * speed) % 1.0
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = self.rect().adjusted(2, 2, -2, -2)
        cx = rect.center().x()
        cy = rect.center().y()
        w = rect.width()
        h = rect.height()

        # Base colors
        grey = QtGui.QColor('#6B727B')
        cyan = QtGui.QColor('#2EE6FF')
        yellow = QtGui.QColor('#F4C61C')
        bg = QtGui.QColor('#0B0D10')

        if self._muted:
            iris_col = grey
        else:
            # mix grey->cyan with rms
            t = min(1.0, self._rms * 2.2)
            iris_col = QtGui.QColor(
                int(grey.red()   * (1-t) + cyan.red()   * t),
                int(grey.green() * (1-t) + cyan.green() * t),
                int(grey.blue()  * (1-t) + cyan.blue()  * t),
            )
            if self._boost:
                # slight yellow shift
                iris_col = QtGui.QColor(
                    int(iris_col.red()   * 0.7 + yellow.red()   * 0.3),
                    int(iris_col.green() * 0.7 + yellow.green() * 0.3),
                    int(iris_col.blue()  * 0.7 + yellow.blue()  * 0.3),
                )

        # Eye outline
        outline = QtGui.QPen(QtGui.QColor('#1A2230'))
        outline.setWidth(2)
        p.setPen(outline)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#111824')))

        eye_path = QtGui.QPainterPath()
        eye_path.moveTo(rect.left(), cy)
        eye_path.quadTo(cx, rect.top(), rect.right(), cy)
        eye_path.quadTo(cx, rect.bottom(), rect.left(), cy)
        p.drawPath(eye_path)

        # Openness: peak closes eyelid, mute closes fully
        if self._muted:
            openness = 0.0
        else:
            openness = 1.0 - min(1.0, self._peak * 1.25)
            if self._stopped:
                openness *= 0.35 + 0.25 * (0.5 + 0.5 * __import__('math').sin(self._phase * 2*__import__('math').pi))

        # Iris
        iris_r = (h * 0.20) * (0.75 + 0.55 * min(1.0, self._rms * 1.8))
        pupil_r = iris_r * 0.45

        # Clamp iris within eye
        p.save()
        clip = QtGui.QPainterPath()
        clip.addPath(eye_path)
        p.setClipPath(clip)

        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(iris_col)
        p.drawEllipse(QtCore.QPointF(cx, cy), iris_r, iris_r)

        p.setBrush(bg)
        p.drawEllipse(QtCore.QPointF(cx, cy), pupil_r, pupil_r)
        p.restore()

        # Eyelids (top/bottom masks)
        if openness < 1.0:
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor('#0F1217'))
            cover = (1.0 - openness) * (h * 0.55)
            p.drawRoundedRect(rect.adjusted(0, 0, 0, -h/2 + cover), 8, 8)
            p.drawRoundedRect(rect.adjusted(0, h/2 - cover, 0, 0), 8, 8)
