import time

from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog, QWidget, QGridLayout, QScrollArea, QAbstractScrollArea,
    QScrollBar, QLabel
)


class _TelaGuida(QWidget):
    clicked = Signal(float, float)

    def __init__(self, guida, tipo):
        super().__init__()
        self.guida = guida
        self.tipo = tipo
        self.setMouseTracking(True)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = self.guida
        if self.tipo == "nomi":
            p.fillRect(evento.rect(), QColor(g.fondo))
            self._nomi(p)
        elif self.tipo == "testa":
            p.fillRect(evento.rect(), QColor(g.pannello))
            self._testa(p)
        else:
            p.fillRect(evento.rect(), QColor(g.fondo))
            self._programmi(p)

    def _testa(self, p):
        g = self.guida
        p.setPen(QPen(QColor("#3a3a3a"), 1))
        t = g.da
        while t <= g.fino:
            x = g.x_di(t)
            p.drawLine(round(x), g.TESTA - 6, round(x), g.TESTA)
            p.setPen(QColor(g.grigio))
            p.drawText(round(x + 6), 19, time.strftime("%H:%M", time.localtime(t)))
            p.setPen(QPen(QColor("#3a3a3a"), 1))
            t += 1800
        x = g.x_di(time.time())
        p.setPen(QPen(QColor(g.accento), 2))
        p.drawLine(round(x), g.TESTA - 8, round(x), g.TESTA)

    def _nomi(self, p):
        g = self.guida
        for i, (nome, url, ide, programmi) in enumerate(g.righe):
            y = i * g.RIGA
            fondo = g.pannello if i % 2 else g.fondo
            p.fillRect(0, y, g.NOMI, g.RIGA, QColor(fondo))
            logo = g.app.logo_di(url)
            if logo is not None:
                p.drawPixmap(8, y + (g.RIGA - logo.height()) // 2, logo)
            else:
                pallino = g.app.pallino_di(nome, url)
                if pallino is not None:
                    p.drawPixmap(8, y + (g.RIGA - pallino.height()) // 2, pallino)
            p.setPen(QColor(g.testo))
            p.drawText(g.LOGO_L + 18, y, g.NOMI - g.LOGO_L - 24, g.RIGA,
                       Qt.AlignVCenter | Qt.AlignLeft, nome[:18])

    def _programmi(self, p):
        g = self.guida
        largo = int(g.x_di(g.fino)) + 20
        alto = max(1, len(g.righe)) * g.RIGA + 20
        p.setPen(QPen(QColor("#2a2a2a"), 1))
        t = g.da
        while t <= g.fino:
            x = round(g.x_di(t))
            p.drawLine(x, 0, x, alto)
            t += 1800
        adesso = time.time()
        for i, (nome, url, ide, programmi) in enumerate(g.righe):
            y0, y1 = i * g.RIGA, (i + 1) * g.RIGA
            fondo = g.pannello if i % 2 else g.fondo
            p.fillRect(0, y0, largo, g.RIGA, QColor(fondo))
            colore = g.app.colore_canale(nome, url)
            for a, b, titolo in programmi:
                xa, xb = max(g.x_di(a), 0), g.x_di(b)
                in_onda = a <= adesso < b
                blocco = g._colore_onda(colore, fondo) if in_onda else g.tasto
                p.fillRect(QRectF(xa + 1, y0 + 6, max(0, xb - xa - 2), g.RIGA - 12),
                           QColor(blocco))
                if xb - xa > 30:
                    testo = titolo
                    while testo and len(testo) * 7 > xb - xa - 14:
                        testo = testo[:-1]
                    if testo != titolo and len(testo) > 2:
                        testo = testo[:-1] + "…"
                    p.setPen(QColor("#ffffff" if in_onda else g.testo))
                    p.drawText(QRectF(xa + 8, y0, max(0, xb - xa - 14), g.RIGA),
                               Qt.AlignVCenter | Qt.AlignLeft, testo)
        x = round(g.x_di(adesso))
        p.setPen(QPen(QColor(g.accento), 2))
        p.drawLine(x, 0, x, alto)


class Guida(QDialog):
    ORA = 300
    RIGA = 64
    NOMI = 250
    TESTA = 28
    LOGO_L = 32

    def __init__(self, app, colori=None):
        super().__init__(app.root if hasattr(app, "root") else app)
        self.app = app
        c = colori or {}
        self.fondo = c.get("fondo", "#121212")
        self.pannello = c.get("pannello", "#1c1b22")
        self.tasto = c.get("tasto", "#2c2c2c")
        self.testo = c.get("testo", "#e0e0e0")
        self.grigio = c.get("grigio", "#9e9e9e")
        self.accento = c.get("accento", "#bb86fc")
        self.LOGO_L = c.get("logo_l", self.LOGO_L)
        self.setWindowTitle(c.get("titolo", "TV guide"))
        self.resize(1100, 620)
        self.setMinimumSize(700, 300)
        griglia = QGridLayout(self)
        griglia.setContentsMargins(0, 0, 0, 0)
        griglia.setSpacing(0)
        angolo = QWidget(self)
        angolo.setFixedSize(self.NOMI, self.TESTA)
        angolo.setStyleSheet("background:%s" % self.pannello)
        griglia.addWidget(angolo, 0, 0)
        self.testata = _TelaGuida(self, "testa")
        self.testata.setFixedHeight(self.TESTA)
        griglia.addWidget(self.testata, 0, 1)
        self.nomi_scroll = QScrollArea(self)
        self.nomi_scroll.setWidgetResizable(False)
        self.nomi_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nomi_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nomi = _TelaGuida(self, "nomi")
        self.nomi_scroll.setWidget(self.nomi)
        griglia.addWidget(self.nomi_scroll, 1, 0)
        self.programmi_scroll = QScrollArea(self)
        self.programmi_scroll.setWidgetResizable(False)
        self.programmi_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.programmi_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tela = _TelaGuida(self, "programmi")
        self.programmi_scroll.setWidget(self.tela)
        griglia.addWidget(self.programmi_scroll, 1, 1)
        self.sbx = QScrollBar(Qt.Horizontal, self)
        self.sby = QScrollBar(Qt.Vertical, self)
        griglia.addWidget(self.sbx, 2, 1)
        griglia.addWidget(self.sby, 1, 2)
        self.sbx.valueChanged.connect(self._x)
        self.sby.valueChanged.connect(self._y)
        self.programmi_scroll.horizontalScrollBar().valueChanged.connect(self.sbx.setValue)
        self.programmi_scroll.verticalScrollBar().valueChanged.connect(self.sby.setValue)
        self._scroll_nomi = self.nomi_scroll.verticalScrollBar()
        self._scroll_testata = self.testata
        self.da = int(time.time() // 1800 * 1800) - 1800
        self.fino = self.da + 6 * 3600
        self.righe = []
        self.raccogli()
        self.tela.clicked.connect(self._clic)
        self.nomi.clicked.connect(self._clic)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.ridisegna)
        self._timer.start(30000)
        self.ridisegna()

    def raccogli(self):
        self.righe = []
        for nome, url, ide in self.app.canali:
            k = ide if ide and ide in self.app.epg else self.app.epg_nomi.get(
                self.app.nome_piatto(nome) if hasattr(self.app, "nome_piatto") else nome)
            if not k:
                from core.epg import nome_piatto
                k = self.app.epg_nomi.get(nome_piatto(nome))
            if not k:
                continue
            prog = [(a, b, t) for a, b, t in self.app.epg.get(k, [])
                    if b > self.da and a < self.fino]
            if prog:
                self.righe.append((nome, url, ide, prog))

    def x_di(self, t):
        return (t - self.da) / 3600.0 * self.ORA

    def _colore_onda(self, colore, fondo, alfa=0.40):
        try:
            a = QColor(colore)
            b = QColor(fondo)
            return QColor(int(a.red() * alfa + b.red() * (1 - alfa)),
                          int(a.green() * alfa + b.green() * (1 - alfa)),
                          int(a.blue() * alfa + b.blue() * (1 - alfa))).name()
        except Exception:
            return "#252030"

    def ridisegna(self):
        self.raccogli()
        largo = int(self.x_di(self.fino)) + 20
        alto = max(1, len(self.righe)) * self.RIGA + 20
        self.tela.resize(largo, alto)
        self.nomi.resize(self.NOMI, alto)
        self.testata.resize(largo, self.TESTA)
        self.sbx.setRange(0, max(0, largo - self.programmi_scroll.viewport().width()))
        self.sby.setRange(0, max(0, alto - self.programmi_scroll.viewport().height()))
        self.nomi.update()
        self.tela.update()
        self.testata.update()

    def _x(self, valore):
        self.programmi_scroll.horizontalScrollBar().setValue(valore)
        self.testata.update()
        self.testata.move(-valore, 0)

    def _y(self, valore):
        self.programmi_scroll.verticalScrollBar().setValue(valore)
        self.nomi_scroll.verticalScrollBar().setValue(valore)

    def _clic(self, x, y):
        i = int(y // self.RIGA)
        if 0 <= i < len(self.righe):
            nome, url, ide, _ = self.righe[i]
            self.app.apri(nome, url, ide)
            QTimer.singleShot(400, self.ridisegna)
