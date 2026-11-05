from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLineEdit


from PySide6.QtCore import QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QFontMetrics, QPixmap, QImage, QIcon, QFont, QCursor, QPolygon
import time
from core.epg import nome_piatto
from core.colors import colore_sfondo_guida
from i18n import _
from core.constants import FONDO, PANNELLO, TESTO, TESTO_ONDA, GRIGIO, SCELTO, ZEBRA, IN_ONDA

SCORRE = object()

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QToolButton, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QMenu, QStyledItemDelegate
)




def _pixmap(valore):
    if valore is None:
        return None
    if isinstance(valore, QPixmap):
        return valore
    if isinstance(valore, QImage):
        return QPixmap.fromImage(valore)
    if isinstance(valore, QIcon):
        return valore.pixmap(QSize(48, 48))
    if isinstance(valore, str):
        pix = QPixmap(valore)
        return pix if not pix.isNull() else None
    if hasattr(valore, "convert") and hasattr(valore, "tobytes"):
        try:
            im = valore.convert("RGBA")
            q = QImage(im.tobytes("raw", "RGBA"), im.width, im.height,
                       im.width * 4, QImage.Format_RGBA8888).copy()
            return QPixmap.fromImage(q)
        except Exception:
            return None
    return None


class Elenco(QListWidget):
    treeviewSelect = Signal()

    def __init__(self, dove, **kw):
        super().__init__(dove)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setStyleSheet(
            ("QListWidget{background:%s;color:%s;border:0;outline:0}" % (PANNELLO, TESTO))
            + "QListWidget::item{border:0;padding:0}"
            + ("QListWidget::item:selected{background:%s;color:white}" % SCELTO)
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
        self.currentItemChanged.connect(self._corrente_cambiato)
        self.setItemDelegate(_ElencoDelegate(self))
        self.setSpacing(0)
        self.setUniformItemSizes(False)
        self.nome_sopra = 10
        self.poster_cache = {}
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
        item.setData(Qt.UserRole + 1, d.get("image"))
        item.setData(Qt.UserRole + 2, d.get("logo"))
        item.setData(Qt.UserRole + 3, d.get("colore") or "#9e9e9e")
        item.setData(Qt.UserRole + 4, d.get("tags", ()))
        colore = QColor(d.get("colore") or "#9e9e9e")
        item.setForeground(colore)
        if d.get("image") is not None and hasattr(d["image"], "toImage"):
            item.setIcon(d["image"])
        item.setBackground(QColor(ZEBRA) if self.posto[iid] % 2 else QColor(FONDO))
        item.setSizeHint(QSize(self.viewport().width(), max(58 if sotto else 42, self.poster_h + 48)))

    def delete(self, *iids):
        if not iids:
            return
        if set(map(str, iids)) >= set(self.voci):
            self.clear()
            self.voci, self.posto, self.dati, self.scelta = [], {}, {}, None
            return
        validi = [str(iid) for iid in iids if str(iid) in self.dati]
        for iid in sorted(validi, key=lambda valore: self.posto[valore], reverse=True):
            row = self.posto[iid]
            self.takeItem(row)
            self.voci.pop(row)
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
        return QListWidget.item(self, self.posto[iid])

    def selection(self):
        return (self.scelta,) if self.scelta in self.dati else ()

    def selection_set(self, iid, vedi=False):
        iid = str(iid) if iid is not None else None
        self.scelta = iid if iid in self.dati else None
        if self.scelta is None or "onda" in self.dati[self.scelta].get("tags", ()):
            self.scelta = None
            self.clearSelection()
            self.setCurrentItem(None)
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
        if "onda" in self.dati.get(iid, {}).get("tags", ()):
            self.scelta = None
            self.clearSelection()
            self.setCurrentItem(None)
        else:
            self.scelta = iid
        if self.singolo:
            self.singolo()

    def _corrente_cambiato(self, corrente, precedente):
        iid = corrente.data(Qt.UserRole) if corrente is not None else None
        if iid is not None and "onda" in self.dati.get(iid, {}).get("tags", ()):
            self.scelta = None
            self.clearSelection()
            return
        if iid != self.scelta:
            self.scelta = iid
            self.treeviewSelect.emit()

    def keyPressEvent(self, evento):
        if evento.key() in (Qt.Key_Left, Qt.Key_Right):
            direzione = -1 if evento.key() == Qt.Key_Left else 1
            if evento.modifiers() & Qt.ShiftModifier:
                if hasattr(self, "avanza"):
                    self.avanza(direzione * 10)
            elif hasattr(self, "salta"):
                self.salta(direzione)
            evento.accept()
            return
        super().keyPressEvent(evento)


class _ElencoDelegate(QStyledItemDelegate):
    def __init__(self, elenco):
        super().__init__(elenco)
        self.elenco = elenco

    @staticmethod
    def _pixmap(valore, lato=None):
        if valore is None:
            return None
        if isinstance(valore, QPixmap):
            pix = valore
        elif isinstance(valore, QImage):
            pix = QPixmap.fromImage(valore)
        elif isinstance(valore, QIcon):
            pix = valore.pixmap(lato or QSize(48, 48))
        elif isinstance(valore, str):
            pix = QPixmap(valore)
        elif hasattr(valore, "convert") and hasattr(valore, "tobytes"):
            try:
                im = valore.convert("RGBA")
                q = QImage(im.tobytes("raw", "RGBA"), im.width, im.height,
                           im.width * 4, QImage.Format_RGBA8888).copy()
                pix = QPixmap.fromImage(q)
            except Exception:
                return None
        else:
            return None
        return pix if not pix.isNull() else None

    def paint(self, painter, option, index):
        e = self.elenco
        iid = index.data(Qt.UserRole)
        d = e.dati.get(iid, {})
        testo = d.get("text") or ""
        nome, _, sotto = testo.partition("\n")
        tags = d.get("tags", ())
        colore = QColor(d.get("colore") or "#9e9e9e")
        rett = option.rect
        selezionato = iid == e.scelta and e.hasFocus() and "onda" not in tags
        sfondo = QColor(SCELTO) if selezionato else (
            QColor(IN_ONDA) if "onda" in tags else
            QColor(ZEBRA) if index.row() % 2 else QColor(FONDO))
        painter.save()
        painter.fillRect(rett, sfondo)
        poster_h = e.poster_h or (e.poster_onda_h if "onda" in tags else 0)
        y_testo = rett.top() + (poster_h + 3 if poster_h else 0) + e.nome_sopra
        logo_x = rett.left() + 8
        colonna = 48
        logo = self._pixmap(d.get("logo"), QSize(40, 40))
        if logo is None:
            logo = self._pixmap(d.get("image"), QSize(24, 24))
        if e.segno == "logo":
            if logo is not None:
                lato = min(40, max(18, rett.height() - 12))
                logo = logo.scaled(lato, lato, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(logo_x + (colonna - logo.width()) // 2,
                                   rett.top() + (rett.height() - logo.height()) // 2,
                                   logo)
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(colore)
                painter.drawEllipse(logo_x + 14, rett.center().y() - 5, 10, 10)
            x_testo = rett.left() + colonna + 18
        else:
            x_testo = rett.left() + 12
        colore_testo = "#ffffff" if selezionato else (TESTO_ONDA if "onda" in tags else colore.name())
        painter.setPen(QColor(colore_testo))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(x_testo, y_testo + 16, nome)
        if sotto:
            font.setBold(False)
            font.setPointSizeF(max(7.0, font.pointSizeF() - 1.0))
            painter.setFont(font)
            painter.setPen(QColor("#ffffff" if selezionato else
                                  TESTO_ONDA if "onda" in tags else colore.name()))
            painter.drawText(x_testo, y_testo + 36, sotto)
        parte = None
        if e.prog_di:
            try:
                parte = e.prog_di(iid)
            except Exception:
                parte = None
        if parte is not None:
            x0 = rett.left() + (colonna if e.segno == "logo" else 0) + 8
            y0 = rett.bottom() - 5
            larg = max(0, rett.right() - x0 - 4)
            painter.fillRect(x0, y0, larg, 2, QColor("#444444"))
            painter.fillRect(x0, y0, int(larg * max(0.0, min(1.0, float(parte)))), 2, colore)
        if poster_h and e.poster_di:
            try:
                chiave = (iid, rett.width(), poster_h)
                poster = e.poster_cache.get(chiave)
                if poster is None:
                    poster = e.poster_di(iid, rett.width() - 8, poster_h)
                    e.poster_cache[chiave] = poster
                img, titolo = poster
                pix = self._pixmap(img)
                if pix is not None:
                    pix = pix.scaled(rett.width() - 8, poster_h,
                                     Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    painter.drawPixmap(rett.left() + 4, rett.top() + 3,
                                       pix, 0, 0, rett.width() - 8, poster_h)
                elif titolo:
                    painter.setPen(QColor(GRIGIO))
                    painter.drawText(rett.left() + 8, rett.top() + poster_h,
                                     str(titolo))
            except Exception:
                pass
        painter.restore()

    def sizeHint(self, option, index):
        d = self.elenco.dati.get(index.data(Qt.UserRole), {})
        tags = d.get("tags", ())
        h = self.elenco.poster_h or (
            self.elenco.poster_onda_h if "onda" in tags else 0)
        return QSize(max(1, option.rect.width()), max(58, h + 48))




from ui.list import Elenco
from ui.dialogs import Finestrella, Tendina
from ui.guide import Guida
