from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStyledItemDelegate, QStyle


_ROLE = Qt.UserRole + 41


class _VoceDelegate(QStyledItemDelegate):
    def __init__(self, elenco):
        super().__init__(elenco)
        self.elenco = elenco

    def sizeHint(self, option, index):
        d = index.data(_ROLE) or {}
        h = self.elenco.altezza_riga
        poster = self.elenco.poster_h or (
            self.elenco.poster_onda_h if "onda" in d.get("tags", ()) else 0)
        return QSize(option.rect.width(), h + poster)

    def paint(self, painter, option, index):
        e = self.elenco
        d = index.data(_ROLE) or {}
        r = option.rect
        painter.save()
        scelto = option.state & QStyle.State_Selected
        onda = "onda" in d.get("tags", ())
        fondo = e.scelto if scelto else (e.onda if onda else
                (e.zebra if index.row() % 2 else e.pannello))
        painter.fillRect(r, QColor(fondo))
        poster_h = e.poster_h or (e.poster_onda_h if onda else 0)
        y = r.y() + poster_h
        if poster_h and e.poster_di:
            try:
                img, titolo = e.poster_di(d.get("iid"), r.width() - 8, poster_h)
                if img is not None:
                    painter.drawPixmap(r.x() + 4, r.y() + 3, img)
                elif titolo:
                    painter.setPen(QColor(e.grigio))
                    painter.drawText(r.adjusted(8, 0, -8, -e.altezza_riga),
                                     Qt.AlignVCenter | Qt.AlignLeft, titolo)
            except Exception:
                pass
        logo = d.get("logo") or d.get("image")
        if e.segno == "logo" and logo is not None:
            try:
                painter.drawPixmap(r.x() + (e.colonna - logo.width()) // 2,
                                   y + (e.altezza_riga - logo.height()) // 2, logo)
            except Exception:
                pass
        nome, _, sotto = (d.get("text") or "").partition("\n")
        nome = nome.lstrip() if e.segno == "logo" else nome
        sotto = sotto.lstrip() if e.segno == "logo" else sotto
        x = r.x() + (e.colonna if e.segno == "logo" else 8)
        if e.segno == "dot" and d.get("image") is not None:
            try:
                painter.drawPixmap(r.x() + 4, y + 2, d["image"])
                x += e.punto + 8
            except Exception:
                pass
        colore = "#ffffff" if scelto else (d.get("colore") or e.grigio)
        f = QFont(e.font)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(colore))
        painter.drawText(x, y + e.nome_px + 2, nome)
        f.setBold(False)
        f.setPixelSize(e.sotto_px)
        painter.setFont(f)
        painter.setPen(QColor(colore))
        painter.drawText(x, y + e.nome_px + e.sotto_px + 8, sotto)
        if e.prog_di:
            try:
                parte = e.prog_di(d.get("iid"))
                if parte is not None:
                    yy = r.bottom() - 2
                    x0 = x + 8
                    larg = max(0, r.right() - x0)
                    painter.fillRect(x0, yy, larg, 2, QColor("#444444"))
                    painter.fillRect(x0, yy, int(larg * max(0, min(1, parte))), 2,
                                     QColor(d.get("colore") or e.grigio))
            except Exception:
                pass
        painter.restore()


class Elenco(QListWidget):
    treeviewSelect = Signal()

    def __init__(self, dove=None, **kw):
        super().__init__(dove)
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setFocusPolicy(Qt.StrongFocus)
        self.voci = []
        self.posto = {}
        self.dati = {}
        self.scelta = None
        self.colonna = None
        self.colonna_dopo = None
        self.prog_di = None
        self.barre = []
        self.poster_h = 0
        self.poster_onda_h = 0
        self.poster_di = None
        self.poster_lbl = []
        self.singolo = None
        self.doppio = None
        self.nome_sopra = 10
        self.segno = "logo"
        self.tinte = set()
        self.corti = {}
        self.pannello = kw.pop("pannello", "#1c1b22")
        self.fondo = kw.pop("fondo", "#121212")
        self.testo = kw.pop("testo", "#e0e0e0")
        self.grigio = kw.pop("grigio", "#9e9e9e")
        self.scelto = kw.pop("scelto", "#0071e3")
        self.zebra = kw.pop("zebra", "#2b2a33")
        self.onda = kw.pop("onda", "#42414d")
        self.colonna = kw.pop("colonna", 44)
        self.punto = kw.pop("punto", 12)
        self.nome_px = kw.pop("nome_px", 14)
        self.sotto_px = kw.pop("sotto_px", 11)
        self.altezza_riga = kw.pop("altezza_riga", 48)
        self.font = self.font()
        self.setStyleSheet("QListWidget{background:%s;color:%s;border:0;outline:0}"
                           "QListWidget::item{border:0;padding:0}"
                           "QListWidget::item:selected{background:transparent}" %
                           (self.pannello, self.testo))
        self.setItemDelegate(_VoceDelegate(self))
        self.currentRowChanged.connect(self._selezione)

    def column(self, *a, **k):
        return None

    def _selezione(self, riga):
        self.scelta = self.voci[riga] if 0 <= riga < len(self.voci) else None

    def get_children(self, *a):
        return tuple(self.voci)

    def exists(self, iid):
        return iid in self.dati

    def insert(self, parent, index, iid=None, text="", image=None, tags=(),
               colore=None, logo=None):
        if iid is None:
            iid = str(len(self.voci))
        d = dict(iid=iid, text=text, image=image, tags=tuple(tags),
                 colore=colore, logo=logo, img=True)
        self.dati[iid] = d
        self.posto[iid] = len(self.voci)
        self.voci.append(iid)
        item = QListWidgetItem()
        item.setData(_ROLE, d)
        self.addItem(item)
        self._aggiorna_altezza()
        return iid

    def delete(self, *iids):
        if not iids:
            return
        if set(iids) >= set(self.voci):
            self.clear()
            self.voci, self.dati, self.scelta, self.posto = [], {}, None, {}
            return
        for iid in iids:
            if iid in self.dati:
                r = self.posto[iid]
                self.takeItem(r)
                self.voci.remove(iid)
                del self.dati[iid]
                if self.scelta == iid:
                    self.scelta = None
        self.posto = {v: i for i, v in enumerate(self.voci)}
        self._aggiorna_altezza()

    def item(self, iid, option=None, **kw):
        d = self.dati[iid]
        if option:
            return d.get(option)
        if kw:
            d.update({k: tuple(v) if k == "tags" else v for k, v in kw.items()})
            item = super().item(self.posto[iid])
            item.setData(_ROLE, d)
            item.setSizeHint(QSize(max(1, self.viewport().width()), self._altezza(d)))
            self.viewport().update()
        return dict(d)

    def selection(self):
        return (self.scelta,) if self.scelta in self.dati else ()

    def selection_set(self, iid, vedi=False):
        self.scelta = iid if iid in self.dati else None
        if self.scelta is None:
            self.clearSelection()
            self.setCurrentRow(-1)
        else:
            r = self.posto[self.scelta]
            self.setCurrentRow(r)
            if vedi:
                self.scrollToItem(super().item(r))
        self.treeviewSelect.emit()

    def selection_remove(self, iid):
        if self.scelta == iid:
            self.selection_set(None)

    def see(self, iid):
        if iid in self.dati:
            self.scrollToItem(super().item(self.posto[iid]))

    def riga(self, iid):
        return self.posto[iid]

    def spanne(self, iid):
        return self.posto[iid], self.posto[iid]

    def corto(self, img):
        return img

    def disegna(self, iid):
        if iid in self.dati:
            item = super().item(self.posto[iid])
            item.setData(_ROLE, self.dati[iid])
            item.setSizeHint(QSize(max(1, self.viewport().width()),
                                   self._altezza(self.dati[iid])))
            self.viewport().update()

    def _altezza(self, d):
        poster = self.poster_h or (self.poster_onda_h if "onda" in d.get("tags", ()) else 0)
        return self.altezza_riga + poster

    def _aggiorna_altezza(self):
        for i, iid in enumerate(self.voci):
            super().item(i).setSizeHint(QSize(max(1, self.viewport().width()),
                                               self._altezza(self.dati[iid])))

    def ridisegna_colonna(self):
        self.viewport().update()

    def metti_poster(self, h):
        if h != self.poster_h:
            self.poster_h = h
            self._aggiorna_altezza()

    def metti_poster_onda(self, h):
        if h != self.poster_onda_h:
            self.poster_onda_h = h
            self._aggiorna_altezza()

    def clic_y(self, y, attiva=False):
        item = self.itemAt(2, int(y))
        if item is not None:
            iid = self.voci[self.row(item)]
            self.selection_set(iid)
            if attiva and self.singolo:
                self.singolo()
        return "break"

    def sposta(self, dove):
        if not self.voci:
            return "break"
        i = self.posto.get(self.scelta, -1)
        i = max(0, min(len(self.voci) - 1, i + dove))
        self.selection_set(self.voci[i], vedi=True)
        return "break"

    def wheelEvent(self, evento):
        super().wheelEvent(evento)
        self.viewport().update()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._aggiorna_altezza()
