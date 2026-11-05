from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLineEdit


class Ricerca(QWidget):
    def __init__(self, dove, cambia, alta=36, vuota="Search",
                 pannello="#1b1b1f", cerca="#252529", testo="#f2f2f2",
                 grigio="#92929a", accento="#a78bfa"):
        super().__init__(dove)
        self.alta, self.cambia, self.vuota = alta, cambia, vuota
        self.pannello, self.cerca = QColor(pannello), QColor(cerca)
        self.testo, self.grigio, self.accento = QColor(testo), QColor(grigio), QColor(accento)
        self.setFixedHeight(alta)
        self.casella = QLineEdit(self)
        self.casella.setFrame(False)
        self.casella.setPlaceholderText(vuota)
        self.casella.setStyleSheet(
            "QLineEdit{background:transparent;border:0;color:%s;selection-background-color:%s}" %
            (self.testo.name(), self.accento.name()))
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
            self.clearFocus()
            return True
        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self.pannello)
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
                 barra="#252529", traccia="#4a4a4a", pieno="#ffffff"):
        super().__init__(dove)
        self.larga, self.alta, self.cambia = larga, alta, cambia
        self.barra, self.traccia, self.pieno = map(QColor, (barra, traccia, pieno))
        self.valore, self.tinta = 85, None
        self.setFixedSize(larga, alta)
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


from PySide6.QtCore import QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QFontMetrics, QPixmap
from core.epg import nome_piatto

SCORRE = object()

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QToolButton, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QMenu
)


class Finestrella(QDialog):
    def __init__(self, root, titolo, corpo, chiedi=None, valore="",
                 ok=None, annulla=None, larga=420, domanda=False, maschera=False):
        super().__init__(root)
        self.setWindowTitle(titolo)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedSize(larga, self.sizeHint().height())
        self.risposta = None
        self.setStyleSheet(
            "QDialog{background:#1b1b1f;color:#f2f2f2}"
            "QLabel{color:#f2f2f2}"
            "QLineEdit{background:#252529;color:#f2f2f2;border:1px solid #393943;"
            "border-radius:5px;padding:7px;selection-background-color:#a78bfa}"
            "QPushButton{background:#252529;color:#f2f2f2;border:0;border-radius:5px;padding:7px 16px}"
            "QPushButton:hover{background:#51466b}"
            "QPushButton[primary=true]{background:#a78bfa;color:#17131f}"
        )
        self.contenuto = QVBoxLayout(self)
        self.contenuto.setContentsMargins(22, 18, 22, 16)
        self.contenuto.setSpacing(8)
        corpo(self)
        self.casella = None
        if chiedi is not None:
            etichetta = QLabel(chiedi, self)
            etichetta.setStyleSheet("color:#92929a")
            self.contenuto.addWidget(etichetta)
            self.casella = QLineEdit(self)
            self.casella.setText(valore)
            self.casella.setEchoMode(QLineEdit.Password if maschera else QLineEdit.Normal)
            self.contenuto.addWidget(self.casella)
            self.casella.selectAll()
        riga = QHBoxLayout()
        riga.addStretch(1)
        if chiedi is not None or domanda:
            b = QPushButton(annulla or "Cancel", self)
            b.clicked.connect(self.lascia)
            riga.addWidget(b)
        b = QPushButton(ok or "OK", self)
        b.setProperty("primary", True)
        b.clicked.connect(self.va_bene)
        riga.addWidget(b)
        self.contenuto.addLayout(riga)
        self.setFixedWidth(larga)
        self.adjustSize()
        if root is not None:
            self.move(root.frameGeometry().center() - self.rect().center())
        if self.casella:
            self.casella.setFocus()
        else:
            self.setFocus()

    def va_bene(self):
        self.risposta = self.casella.text() if self.casella is not None else True
        self.accept()

    def lascia(self):
        self.risposta = None
        self.reject()

    def chiudi_dopo(self):
        self.accept()


class Tendina(QFrame):
    ALTA = 30

    def __init__(self, root):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.root = root
        self.top = None
        self.al_chiudere = None
        self.chi = None
        self.altrove = None
        self.fuori_da = None
        self.aveva_fuoco = False
        self.setObjectName("xvbTendina")
        self.setStyleSheet(
            "QFrame#xvbTendina{background:#1b1b1f;border:1px solid #51466b}"
            "QPushButton{background:transparent;color:#f2f2f2;text-align:left;"
            "border:0;padding:5px 12px;min-height:20px}"
            "QPushButton:hover{background:#51466b;color:white}"
            "QPushButton:disabled{color:#92929a}"
        )

    def aperta(self):
        return self.isVisible()

    def apri(self, x, y, voci, sopra=False, destra=False, al_chiudere=None,
             chi=None, altrove=None):
        self.chiudi()
        self.al_chiudere, self.chi, self.altrove = al_chiudere, chi, altrove
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        piatte = []
        for voce in voci:
            if voce and voce[0] is SCORRE:
                piatte.extend(voce[1])
            else:
                piatte.append(voce)
        larghezza = max([QFontMetrics(self.font()).horizontalAdvance(
            v[0][3:] if v[0][:3] in ("*  ", "   ") else v[0]) + 70
            for v in piatte if v] + [180])
        for voce in voci:
            if voce is None:
                linea = QFrame(self)
                linea.setFrameShape(QFrame.HLine)
                linea.setStyleSheet("color:#51466b;margin:4px 10px")
                layout.addWidget(linea)
            elif voce[0] is SCORRE:
                lista, numero = voce[1], voce[2]
                area = QScrollArea(self)
                area.setWidgetResizable(True)
                area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                area.setMaximumHeight(max(3, numero) * self.ALTA)
                contenitore = QWidget()
                col = QVBoxLayout(contenitore)
                col.setContentsMargins(0, 0, 0, 0)
                col.setSpacing(0)
                for elemento in lista:
                    self._riga(col, elemento)
                area.setWidget(contenitore)
                layout.addWidget(area)
            else:
                self._riga(layout, voce)
        self.setMinimumWidth(larghezza)
        self.adjustSize()
        pos = QPoint(x, y - self.height() if sopra else y)
        if destra:
            pos.setX(x - self.width())
        screen = self.root.screen().availableGeometry()
        pos.setX(max(screen.left(), min(pos.x(), screen.right() - self.width() + 1)))
        pos.setY(max(screen.top(), min(pos.y(), screen.bottom() - self.height() + 1)))
        self.move(pos)
        self.top = self
        self.show()
        self.setFocus()
        self.finestra_era = self.root.geometry()
        self._sorveglia()

    def _riga(self, layout, voce):
        testo, cosa = voce
        spunta = testo.startswith("*  ")
        if testo[:3] in ("*  ", "   "):
            testo = testo[3:]
        b = QPushButton(("✓   " if spunta else "    ") + testo, self)
        b.setFixedHeight(self.ALTA)
        b.setEnabled(bool(cosa))
        if cosa:
            b.clicked.connect(lambda _=False, c=cosa: self.scegli(c))
        layout.addWidget(b)

    def _sorveglia(self):
        if not self.isVisible():
            return
        if self.root.geometry() != self.finestra_era:
            self.chiudi()
            return
        self._watch_timer = QTimer(self)
        self._watch_timer.setSingleShot(True)
        self._watch_timer.timeout.connect(self._sorveglia)
        self._watch_timer.start(150)

    def accendi(self, riga, a, b, si):
        riga.setStyleSheet("background:#51466b" if si else "background:#1b1b1f")

    def scegli(self, cosa):
        self.chiudi()
        QTimer.singleShot(40, cosa)

    def fuori(self, ev=None):
        self.chiudi()

    def chiudi(self):
        if not self.isVisible():
            return
        f, self.al_chiudere = self.al_chiudere, None
        self.hide()
        self.top = None
        self.chiusa = (self.chi, __import__("time").time())
        self.chi = None
        if f:
            f()


class Elenco(QListWidget):
    def __init__(self, dove, **kw):
        super().__init__(dove)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setStyleSheet(
            "QListWidget{background:#1b1b1f;color:#f2f2f2;border:0;outline:0}"
            "QListWidget::item{border:0;padding:0}"
            "QListWidget::item:selected{background:#51466b;color:white}"
        )
        self.voci, self.posto, self.dati = [], {}, {}
        self.scelta = None
        self.prog_di = None
        self.poster_di = None
        self.singolo = None
        self.doppio = None
        self.segno = "logo"
        self.poster_h = 0
        self.poster_onda_h = 0
        self.itemClicked.connect(self._selezionato)
        self.itemDoubleClicked.connect(lambda _i: self.doppio() if self.doppio else None)

    def column(self, *a, **k):
        return None

    def get_children(self, *a):
        return tuple(self.voci)

    def exists(self, iid):
        return iid in self.dati

    def insert(self, parent, index, iid=None, text="", image=None, tags=(), colore=None, logo=None):
        iid = str(len(self.voci)) if iid is None else str(iid)
        d = dict(text=text, image=image, tags=tuple(tags), colore=colore, logo=logo, img=True)
        self.dati[iid] = d
        self.posto[iid] = len(self.voci)
        self.voci.append(iid)
        item = QListWidgetItem()
        self.addItem(item)
        self._aggiorna_item(iid, item)
        return iid

    def _aggiorna_item(self, iid, item):
        d = self.dati[iid]
        nome, _, sotto = (d["text"] or "").partition("\n")
        item.setText(nome + ("\n" + sotto if sotto else ""))
        item.setData(Qt.UserRole, iid)
        colore = QColor(d.get("colore") or "#92929a")
        item.setForeground(colore)
        if d.get("image") is not None and hasattr(d["image"], "toImage"):
            item.setIcon(d["image"])
        item.setBackground(QColor("#202025") if self.posto[iid] % 2 else QColor("#1b1b1f"))
        item.setSizeHint(QSize(self.viewport().width(), 58 if sotto else 42))

    def delete(self, *iids):
        if not iids:
            return
        if set(map(str, iids)) >= set(self.voci):
            self.clear()
            self.voci, self.posto, self.dati, self.scelta = [], {}, {}, None
            return
        for iid in map(str, iids):
            if iid not in self.dati:
                continue
            row = self.posto[iid]
            self.takeItem(row)
            self.voci.remove(iid)
            del self.dati[iid]
            if self.scelta == iid:
                self.scelta = None
        self.posto = {v: i for i, v in enumerate(self.voci)}

    def item(self, iid, option=None, **kw):
        d = self.dati[str(iid)]
        if option:
            return d.get(option)
        if not kw:
            return dict(d)
        d.update({k: tuple(v) if k == "tags" else v for k, v in kw.items()})
        self._aggiorna_item(str(iid), self.item_for(str(iid)))

    def item_for(self, iid):
        return self.item(self.posto[iid])

    def selection(self):
        return (self.scelta,) if self.scelta in self.dati else ()

    def selection_set(self, iid, vedi=False):
        iid = str(iid) if iid is not None else None
        self.scelta = iid if iid in self.dati else None
        if self.scelta is None:
            self.clearSelection()
        else:
            item = self.item_for(self.scelta)
            self.setCurrentItem(item)
            if vedi:
                self.scrollToItem(item)
        self.treeviewSelect.emit()

    def selection_remove(self, iid):
        if self.scelta == str(iid):
            self.selection_set(None)

    def see(self, iid):
        if str(iid) in self.dati:
            self.scrollToItem(self.item_for(str(iid)))

    def riga(self, iid):
        return 3 * self.posto[str(iid)] + 1

    def spanne(self, iid):
        r = self.riga(iid)
        return (r, r + 2)

    def corto(self, img):
        return img

    def disegna(self, iid):
        if iid in self.dati:
            self._aggiorna_item(iid, self.item_for(iid))

    def ridisegna_colonna(self):
        self.viewport().update()

    def metti_poster(self, h):
        self.poster_h = h
        self.viewport().update()

    def metti_poster_onda(self, h):
        self.poster_onda_h = h
        self.viewport().update()

    def _nuovo_poster(self):
        return QLabel(self)

    def _poster(self):
        self.viewport().update()

    def _nuova_barra(self):
        return QFrame(self), QFrame(self)

    def _barre(self):
        self.viewport().update()

    def _colonna_loghi(self):
        self.viewport().update()

    def clic_y(self, y, attiva=False):
        item = self.itemAt(3, y)
        if item:
            self.selection_set(item.data(Qt.UserRole))
            if attiva and self.singolo:
                self.singolo()
        return "break"

    def clic(self, ev=None):
        item = self.itemAt(ev.position().toPoint()) if ev is not None else None
        if item:
            self.selection_set(item.data(Qt.UserRole))
            if self.singolo:
                self.singolo()
        return "break"

    def sposta(self, dove):
        if not self.voci:
            return "break"
        i = self.voci.index(self.scelta) if self.scelta in self.dati else -1
        i = max(0, min(len(self.voci) - 1, i + dove))
        self.selection_set(self.voci[i], vedi=True)
        return "break"

    def _selezionato(self, item):
        iid = item.data(Qt.UserRole)
        self.scelta = iid
        if self.singolo:
            self.singolo()


class Guida(QDialog):
    ORA, RIGA, NOMI, TESTA = 300, 64, 250, 28

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.setWindowTitle("TV guide")
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
            self.nomi.addItem(nome)

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
        p.fillRect(self.rect(), QColor("#121212"))
        altezza = max(1, len(g.righe)) * g.RIGA
        t = g.da
        while t <= g.fino:
            x = g.x_di(t)
            p.setPen(QPen(QColor("#2a2a2a"), 1))
            p.drawLine(round(x), 0, round(x), altezza)
            p.setPen(QColor("#92929a"))
            p.drawText(round(x + 6), 18, time.strftime("%H:%M", time.localtime(t)))
            t += 1800
        adesso = time.time()
        for i, (nome, url, ide, prog) in enumerate(g.righe):
            y0 = i * g.RIGA
            p.fillRect(0, y0, self.width(), g.RIGA, QColor("#1b1b1f" if i % 2 else "#121212"))
            colore = QColor(g.app.colore_canale(nome, url))
            for a, b, titolo in prog:
                xa, xb = max(g.x_di(a), 0), g.x_di(b)
                in_onda = a <= adesso < b
                sfondo = QColor(colore)
                if in_onda:
                    sfondo = QColor(
                        int(colore.red() * .4 + 18 * .6),
                        int(colore.green() * .4 + 18 * .6),
                        int(colore.blue() * .4 + 18 * .6))
                else:
                    sfondo = QColor("#303036")
                p.fillRect(QRect(round(xa + 1), y0 + 6, max(1, round(xb - xa - 2)), g.RIGA - 12), sfondo)
                if xb - xa > 30:
                    p.setPen(QColor("#ffffff" if in_onda else "#f2f2f2"))
                    testo = QFontMetrics(p.font()).elidedText(titolo, Qt.ElideRight, max(0, round(xb - xa - 14)))
                    p.drawText(round(xa + 8), y0 + g.RIGA // 2 + 5, testo)
        x = g.x_di(adesso)
        p.setPen(QPen(QColor("#a78bfa"), 2))
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
        p.fillRect(self.rect(), QColor("#1b1b1f"))
        t = self.guida.da
        while t <= self.guida.fino:
            x = self.guida.x_di(t)
            p.setPen(QColor("#92929a"))
            p.drawText(round(x + 6), 19, time.strftime("%H:%M", time.localtime(t)))
            t += 1800
