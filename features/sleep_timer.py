from PySide6.QtCore import QObject, QTimer, Signal


class SleepTimer(QObject):
    expired = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.expired.emit)

    @property
    def active(self):
        return self._timer.isActive()

    def start(self, minutes):
        self._timer.start(int(minutes) * 60 * 1000)

    def cancel(self):
        self._timer.stop()
