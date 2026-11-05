import os

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from core.config import QUI


class Sfondo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._predefinita = os.path.join(QUI, "icone", "screen.png")
        self._percorso = None
        self._pixmap = QPixmap()
        self._effetto = QGraphicsOpacityEffect(self)
        self._effetto.setOpacity(1.0)
        self.setGraphicsEffect(self._effetto)
        self._animazione = QPropertyAnimation(self._effetto, b"opacity", self)
        self._animazione.setDuration(1200)
        self._animazione.setStartValue(0.0)
        self._animazione.setEndValue(1.0)
        self._animazione.setEasingCurve(QEasingCurve.InOutCubic)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background:#000000")

    def imposta(self, immagine=None, dissolvi=False, attesa=300):
        percorso = immagine if isinstance(immagine, str) else None
        if percorso == self._percorso and not self._pixmap.isNull():
            return
        self._percorso = percorso
        nuovo = QPixmap(percorso or self._predefinita)
        if nuovo.isNull():
            nuovo = QPixmap(self._predefinita)
        self._pixmap = nuovo
        if dissolvi:
            self.dissolvi(attesa)
        else:
            self._animazione.stop()
            self._effetto.setOpacity(1.0)
        self.update()

    def imposta_pixmap(self, immagine, dissolvi=False, attesa=300):
        if isinstance(immagine, QPixmap):
            if not self._pixmap.isNull() and immagine.cacheKey() == self._pixmap.cacheKey():
                return
            self._pixmap = immagine
        else:
            self._pixmap = QPixmap(self._predefinita)
        self._percorso = None
        if dissolvi:
            self.dissolvi(attesa)
        else:
            self._animazione.stop()
            self._effetto.setOpacity(1.0)
        self.update()

    def dissolvi(self, attesa=300):
        self._animazione.stop()
        self._effetto.setOpacity(0.0)
        QTimer.singleShot(max(0, int(attesa)), self._avvia_dissolvenza)

    def _avvia_dissolvenza(self):
        if self.isVisible():
            self._animazione.start()
        else:
            self._effetto.setOpacity(1.0)

    def paintEvent(self, evento):
        pittore = QPainter(self)
        pittore.fillRect(self.rect(), QColor("#000000"))
        if not self._pixmap.isNull():
            immagine = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - immagine.width()) // 2
            y = (self.height() - immagine.height()) // 2
            pittore.drawPixmap(x, y, immagine)
        pittore.end()
