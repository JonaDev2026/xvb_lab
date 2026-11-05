from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLineEdit


from PySide6.QtCore import QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QFontMetrics, QPixmap, QImage, QIcon, QFont, QCursor, QPolygon
import time
from core.epg import nome_piatto
from core.colors import colore_sfondo_guida
from core.constants import FONDO, PANNELLO, TASTO, TESTO, GRIGIO, ACCENTO
from i18n import _

SCORRE = object()

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QToolButton, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QMenu, QStyledItemDelegate
)


class Guida(QDialog):
    ORA, RIGA, NOMI, TESTA = 300, 64, 250, 28

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.setWindowTitle(_("TV guide"))
        self.resize(1100, 620)
        self.setMinimumSize(700, 300)
        self.da = int(__import__("time").time() // 1800 * 1800) - 1800
        self.fino = self.da + 6 * 3600
        self.righe = []
        griglia = QHBoxLayout(self)
        griglia.setContentsMargins(0, 0, 0, 0)
        self.nomi = QListWidget(self)
        self.nomi.setFixedWidth(self.NOMI)
        self.nomi.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nomi.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nomi.setStyleSheet(
            "QListWidget{background:%s;color:%s;border:0;outline:0}"
            "QListWidget::item{border:0;padding:0 8px}"
            "QListWidget::item:selected{background:%s;color:white}" %
            (FONDO, TESTO, ACCENTO))
        self.tela = _TelaGuida(self)
        self.area_tela = QScrollArea(self)
        self.area_tela.setWidgetResizable(False)
        self.area_tela.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.area_tela.setWidget(self.tela)
        self.testa = _TestaGuida(self)
        self.area_testa = QScrollArea(self)
        self.area_testa.setWidgetResizable(False)
        self.area_testa.setFixedHeight(self.TESTA + 2)
        self.area_testa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.area_testa.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.area_testa.setWidget(self.testa)
        destra = QVBoxLayout()
        destra.setContentsMargins(0, 0, 0, 0)
        destra.setSpacing(0)
        destra.addWidget(self.area_testa)
        destra.addWidget(self.area_tela, 1)
        griglia.addWidget(self.nomi)
        griglia.addLayout(destra, 1)
        self.nomi.verticalScrollBar().valueChanged.connect(self.area_tela.verticalScrollBar().setValue)
        self.area_tela.verticalScrollBar().valueChanged.connect(self.nomi.verticalScrollBar().setValue)
        self.area_tela.horizontalScrollBar().valueChanged.connect(self.area_testa.horizontalScrollBar().setValue)
        self.raccogli()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.ridisegna)
        self._timer.start(30000)
        self.nomi.itemClicked.connect(self._clic_nome)

    def raccogli(self):
        self.righe = []
        for nome, url, ide in self.app.canali:
            k = ide if ide and ide in self.app.epg else self.app.epg_nomi.get(nome_piatto(nome))
            if not k:
                continue
            prog = [(a, b, t) for a, b, t in self.app.epg.get(k, [])
                    if b > self.da and a < self.fino]
            if prog:
                self.righe.append((nome, url, ide, prog))
        self.nomi.clear()
        for nome, url, ide, prog in self.righe:
            voce = QListWidgetItem(nome)
            logo = self.app.logo_di(url) if hasattr(self.app, "logo_di") else None
            if logo is not None:
                voce.setIcon(QIcon(logo))
            voce.setSizeHint(QSize(self.NOMI, self.RIGA))
            voce.setBackground(QColor(PANNELLO if self.nomi.count() % 2 else FONDO))
            self.nomi.addItem(voce)
        self.tela.setMinimumSize(6 * self.ORA, max(1, len(self.righe)) * self.RIGA + 20)
        self.testa.setMinimumSize(6 * self.ORA, self.TESTA)

    def x_di(self, t):
        return (t - self.da) / 3600.0 * self.ORA

    def ridisegna(self):
        self.raccogli()
        self.tela.update()
        self.testa.update()

    def disegna(self):
        self.ridisegna()

    def _clic_nome(self, item):
        i = self.nomi.row(item)
        if 0 <= i < len(self.righe):
            self._apri(i)

    def _apri(self, i):
        nome, url, ide, _prog = self.righe[i]
        if hasattr(self.app, "apri_canale_guida"):
            self.app.apri_canale_guida(nome, url, ide)
        else:
            self.app.apri(nome, url, ide)
        QTimer.singleShot(400, self.tela.update)

    def chiudi(self):
        self.close()


class _TelaGuida(QWidget):
    def __init__(self, guida):
        super().__init__()
        self.guida = guida
        self.setMinimumSize(6 * guida.ORA, 1)

    def paintEvent(self, evento):
        from PySide6.QtGui import QPainter, QPen
        import time
        g, p = self.guida, QPainter(self)
        p.fillRect(self.rect(), QColor(FONDO))
        altezza = max(1, len(g.righe)) * g.RIGA
        t = g.da
        while t <= g.fino:
            x = g.x_di(t)
            p.setPen(QPen(QColor("#2a2a2a"), 1))
            p.drawLine(round(x), 0, round(x), altezza)
            p.setPen(QColor(GRIGIO))
            p.drawText(round(x + 6), 18, time.strftime("%H:%M", time.localtime(t)))
            t += 1800
        adesso = time.time()
        for i, (nome, url, ide, prog) in enumerate(g.righe):
            y0 = i * g.RIGA
            fondo = PANNELLO if i % 2 else FONDO
            p.fillRect(0, y0, self.width(), g.RIGA, QColor(fondo))
            colore = QColor(g.app.colore_canale(nome, url))
            for a, b, titolo in prog:
                xa, xb = max(g.x_di(a), 0), g.x_di(b)
                in_onda = a <= adesso < b
                sfondo = QColor(colore_sfondo_guida(colore.name(), fondo, 0.40)) if in_onda else QColor(TASTO)
                p.fillRect(QRect(round(xa + 1), y0 + 6, max(1, round(xb - xa - 2)), g.RIGA - 12), sfondo)
                if xb - xa > 30:
                    p.setPen(QColor("#ffffff" if in_onda else TESTO))
                    testo = QFontMetrics(p.font()).elidedText(titolo, Qt.ElideRight, max(0, round(xb - xa - 14)))
                    p.drawText(round(xa + 8), y0 + g.RIGA // 2 + 5, testo)
        x = g.x_di(adesso)
        p.setPen(QPen(QColor(ACCENTO), 2))
        p.drawLine(round(x), 0, round(x), altezza)
        p.end()

    def mousePressEvent(self, e):
        g = self.guida
        i = int(e.position().y() // g.RIGA)
        if 0 <= i < len(g.righe):
            g._apri(i)


class _TestaGuida(QWidget):
    def __init__(self, guida):
        super().__init__()
        self.guida = guida
        self.setFixedHeight(guida.TESTA)

    def paintEvent(self, evento):
        import time
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1c1b22"))
        t = self.guida.da
        while t <= self.guida.fino:
            x = self.guida.x_di(t)
            p.setPen(QPen(QColor("#3a3a3a"), 1))
            p.drawLine(round(x), self.guida.TESTA - 6, round(x), self.guida.TESTA)
            p.setPen(QColor("#9e9e9e"))
            p.drawText(round(x + 6), 19, time.strftime("%H:%M", time.localtime(t)))
            t += 1800
        x = round(self.guida.x_di(time.time()))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(ACCENTO))
        p.drawPolygon(QPolygon([
            QPoint(x - 6, self.guida.TESTA - 8),
            QPoint(x + 6, self.guida.TESTA - 8),
            QPoint(x, self.guida.TESTA)
        ]))


