from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class HudVideo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer_text = ""
        self.recording_text = ""
        self.phase = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.hide()

    def set_state(self, timer_text="", recording_text="", phase=0):
        self.timer_text = str(timer_text or "")
        self.recording_text = str(recording_text or "")
        self.phase = int(phase) % 12
        righe = int(bool(self.timer_text)) + int(bool(self.recording_text))
        if not righe:
            self.hide()
            return
        self.setFixedSize(132, righe * 28 + (righe - 1) * 6)
        self.posiziona()
        self.show()
        self.raise_()
        self.update()

    def posiziona(self, split=False, schermo=0):
        padre = self.parentWidget()
        if padre is None:
            return
        area = padre.width()
        inizio = 0
        if split:
            meta = area // 2
            if schermo == 0:
                area = meta
            else:
                inizio = meta
                area -= meta
        self.move(max(0, inizio + area - self.width() - 10), 10)

    def paintEvent(self, evento):
        pittore = QPainter(self)
        pittore.setRenderHint(QPainter.Antialiasing)
        font = QFont(self.font())
        font.setPointSize(10)
        font.setBold(True)
        pittore.setFont(font)
        righe = []
        if self.timer_text:
            righe.append(("timer", self.timer_text, QColor("#ff9f0a")))
        if self.recording_text:
            righe.append(("rec", self.recording_text, QColor("#ff453a")))
        for indice, (tipo, testo, colore) in enumerate(righe):
            y = indice * 34
            pittore.setPen(Qt.NoPen)
            pittore.setBrush(QColor(0, 0, 0, 132))
            pittore.drawRoundedRect(QRect(0, y, self.width(), 28), 14, 14)
            if tipo == "timer":
                pittore.setBrush(Qt.NoBrush)
                pittore.setPen(QPen(colore, 2))
                pittore.drawEllipse(10, y + 8, 12, 12)
                pittore.drawLine(16, y + 10, 16, y + 14)
                pittore.drawLine(16, y + 14, 20, y + 16)
            else:
                alpha = int(80 + 175 * (0.5 + 0.5 * (self.phase / 11.0)))
                pittore.setPen(Qt.NoPen)
                pittore.setBrush(QColor(colore.red(), colore.green(), colore.blue(), alpha))
                pittore.drawEllipse(12, y + 9, 10, 10)
            pittore.setPen(colore)
            pittore.drawText(QRect(34, y, self.width() - 42, 28),
                            Qt.AlignVCenter | Qt.AlignLeft, testo)
        pittore.end()
