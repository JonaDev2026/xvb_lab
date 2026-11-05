from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from core.constants import PANNELLO, TASTO
from core.config import scrivi_config


class Maniglia(QWidget):
    def __init__(self, app, pannello, chiave, verso):
        super().__init__(app.contenuto)
        self.app = app
        self.pannello = pannello
        self.chiave = chiave
        self.verso = verso
        self.setFixedWidth(8)
        self.setCursor(Qt.SizeHorCursor)
        self._trascina = False
        self.setMouseTracking(True)

    def enterEvent(self, evento):
        self.update()
        super().enterEvent(evento)

    def leaveEvent(self, evento):
        self.update()
        super().leaveEvent(evento)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(TASTO if self.underMouse() else PANNELLO))
        colore = QColor("#9a9aa8" if self.underMouse() else "#5a5a64")
        p.setPen(Qt.NoPen)
        p.setBrush(colore)
        centro = self.height() // 2
        for dy in (-8, 0, 8):
            p.drawEllipse(QPoint(4, centro + dy), 2, 2)

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self._trascina = True
            evento.accept()

    def mouseMoveEvent(self, evento):
        if not self._trascina or not (evento.buttons() & Qt.LeftButton):
            return
        x = evento.globalPosition().toPoint().x()
        origine = self.pannello.mapToGlobal(QPoint(0, 0)).x()
        if self.verso > 0:
            larga = x - origine
        else:
            larga = origine + self.pannello.width() - x
        massima = max(140, int(self.app.width() * 0.6))
        self.pannello.setFixedWidth(max(140, min(massima, int(larga))))

    def mouseReleaseEvent(self, evento):
        if evento.button() == Qt.LeftButton and self._trascina:
            self._trascina = False
            self.app.sessione.config[self.chiave] = self.pannello.width()
            scrivi_config(self.app.sessione.config)
            evento.accept()
