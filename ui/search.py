from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLineEdit, QSizePolicy


class Ricerca(QWidget):
    def __init__(self, dove, cambia, alta=36, vuota="Search",
                 pannello="#1c1b22", cerca="#42414d", testo="#e0e0e0",
                 grigio="#9e9e9e", accento="#bb86fc"):
        super().__init__(dove)
        self.alta, self.cambia, self.vuota = alta, cambia, vuota
        self.pannello, self.cerca = QColor(pannello), QColor(cerca)
        self.testo, self.grigio, self.accento = QColor(testo), QColor(grigio), QColor(accento)
        self.setFixedHeight(alta)
        self.casella = QLineEdit(self)
        self.casella.setFrame(False)
        self.casella.setPlaceholderText(vuota)
        self.casella.setStyleSheet(
            "QLineEdit{background:transparent;border:0;color:%s;selection-background-color:%s}"
            "QLineEdit::placeholder{color:%s}" %
            (self.testo.name(), self.accento.name(), self.grigio.name()))
        self.casella.textChanged.connect(lambda _v: self.cambia())
        self.casella.installEventFilter(self)
        self._posiziona()

    def _posiziona(self):
        r = self.alta // 2
        self.casella.setGeometry(r + 16, self.alta // 2 - 10,
                                 max(0, self.width() - 2 * r - 22), 20)

    def resizeEvent(self, e):
        self._posiziona()
        super().resizeEvent(e)

    def eventFilter(self, obj, e):
        if obj is self.casella and e.type() == e.Type.KeyPress and e.key() == Qt.Key_Escape:
            self.casella.clear()
            self.cambia()
            self.casella.clearFocus()
            return True
        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.fillRect(self.rect(), self.pannello)
        p.setBrush(self.cerca)
        p.drawRoundedRect(self.rect(), self.alta / 2, self.alta / 2)
        r = self.alta / 2
        p.setPen(QPen(self.grigio, 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r - 4, self.alta / 2 - 7, 10, 10)
        p.drawLine(r + 4, self.alta / 2 + 3, r + 9, self.alta / 2 + 8)

    def get(self):
        return self.casella.text()


class Cursore(QWidget):
    valoreCambiato = Signal(int)

    def __init__(self, dove, cambia, larga=170, alta=26,
                 barra="#1c1b22", traccia="#4a4a4a", pieno="#ffffff"):
        super().__init__(dove)
        self.larga, self.alta, self.cambia = larga, alta, cambia
        self.barra, self.traccia, self.pieno = map(QColor, (barra, traccia, pieno))
        self.valore, self.tinta = 85, None
        self.setFixedHeight(alta)
        self.setMinimumWidth(0)
        self.setMaximumWidth(larga)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.resize(larga, alta)
        self.setCursor(Qt.PointingHandCursor)
        self.valoreCambiato.connect(self.cambia)

    def tocca(self, x):
        k = (x - 10) / float(self.larga - 20)
        self.set(round(max(0.0, min(1.0, k)) * 100))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.tocca(e.position().x())

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.tocca(e.position().x())

    def wheelEvent(self, e):
        self.set(self.valore + (5 if e.angleDelta().y() > 0 else -5))
        e.accept()

    def set(self, v):
        v = int(max(0, min(100, v)))
        if v != self.valore:
            self.valore = v
            self.valoreCambiato.emit(v)
        self.update()

    def get(self):
        return self.valore

    def value(self):
        return self.valore

    def setValue(self, valore):
        self.set(valore)

    def sfondo(self, tinta):
        self.tinta = tinta
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.tinta:
            for r in range(self.alta):
                try:
                    c = QColor(self.tinta(self.mapToParent(self.rect().topLeft()).y() + r))
                except Exception:
                    c = self.barra
                p.setPen(QPen(c, 1))
                p.drawLine(0, r, self.larga, r)
        else:
            p.fillRect(self.rect(), self.barra)
        y, x0, x1 = self.alta // 2, 10, self.larga - 10
        x = x0 + (x1 - x0) * self.valore / 100.0
        p.setPen(QPen(self.traccia, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(x0, y, x1, y)
        if x > x0:
            p.setPen(QPen(self.pieno, 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(x0, y, round(x), y)


