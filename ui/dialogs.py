from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLineEdit


from PySide6.QtCore import QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QFontMetrics, QPixmap, QImage, QIcon, QFont, QCursor, QPolygon
import time
from core.epg import nome_piatto
from core.colors import colore_sfondo_guida
from i18n import _
from core.constants import PANNELLO, CERCA, TESTO, GRIGIO, ACCENTO, SCELTO, IN_ONDA, TESTO_ONDA

SCORRE = object()

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QToolButton, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QMenu, QStyledItemDelegate
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
            "QDialog{background:{PANNELLO};color:{TESTO}}"
            "QLabel{color:{TESTO}}"
            "QLineEdit{background:%s;color:%s;border:1px solid %s;" % (CERCA, TESTO, SCELTO)
            "border-radius:5px;padding:7px;selection-background-color:{TESTO_ONDA}}"
            "QPushButton{background:%s;color:%s;border:0;border-radius:5px;padding:7px 16px}" % (CERCA, TESTO)
            "QPushButton:hover{background:{SCELTO}}"
            "QPushButton[primary=true]{background:%s;color:%s}" % (IN_ONDA, TESTO_ONDA)
        )
        self.contenuto = QVBoxLayout(self)
        self.contenuto.setContentsMargins(22, 18, 22, 16)
        self.contenuto.setSpacing(8)
        corpo(self)
        self.casella = None
        if chiedi is not None:
            etichetta = QLabel(chiedi, self)
            etichetta.setStyleSheet("color:{GRIGIO}")
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
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(150)
        self._watch_timer.timeout.connect(self._sorveglia)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(0)
        self.setObjectName("xvbTendina")
        self.setStyleSheet(
            "QFrame#xvbTendina{background:%s;border:1px solid %s}" % (PANNELLO, SCELTO)
            "QPushButton{background:transparent;color:%s;text-align:left;" % TESTO
            "border:0;padding:5px 12px;min-height:20px}"
            "QPushButton:hover{background:%s;color:white}" % SCELTO
            "QPushButton:disabled{color:%s}" % GRIGIO
        )

    def aperta(self):
        return self.isVisible()

    def apri(self, x, y, voci, sopra=False, destra=False, al_chiudere=None,
             chi=None, altrove=None):
        self.chiudi()
        self.al_chiudere, self.chi, self.altrove = al_chiudere, chi, altrove
        layout = self._layout
        while layout.count():
            voce_layout = layout.takeAt(0)
            widget = voce_layout.widget()
            if widget is not None:
                widget.deleteLater()
            elif voce_layout.layout() is not None:
                voce_layout.layout().deleteLater()
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
                linea.setStyleSheet("color:%s;margin:4px 10px" % SCELTO)
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
                selezionata = None
                for indice, elemento in enumerate(lista):
                    bottone = self._riga(col, elemento)
                    if elemento and elemento[0].startswith("*  ") and selezionata is None:
                        selezionata = indice
                area.setWidget(contenitore)
                layout.addWidget(area)
                if selezionata is not None:
                    QTimer.singleShot(
                        0, lambda a=area, i=selezionata, n=numero:
                        a.verticalScrollBar().setValue(
                            max(0, (i - n // 2) * self.ALTA)))
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
        self._watch_timer.start()

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
        return b

    def _sorveglia(self):
        if not self.isVisible():
            return
        if self.root.geometry() != self.finestra_era:
            self.chiudi()
            return
        posizione = QCursor.pos()
        def contiene(widget):
            if widget is None or not widget.isVisible():
                return False
            return widget.frameGeometry().contains(posizione)
        if contiene(self) or contiene(self.chi):
            self.fuori_da = None
        elif self.altrove:
            try:
                if self.altrove(posizione.x(), posizione.y(), subito=True):
                    return
            except TypeError:
                if self.altrove(posizione.x(), posizione.y()):
                    return
            if self.fuori_da is None:
                self.fuori_da = time.monotonic()
            elif time.monotonic() - self.fuori_da > 2.0:
                self.chiudi()
                return
        elif self.fuori_da is None:
            self.fuori_da = time.monotonic()
        elif time.monotonic() - self.fuori_da > 2.0:
            self.chiudi()
            return

    def accendi(self, riga, a, b, si):
        riga.setStyleSheet("background:%s" % (SCELTO if si else PANNELLO))

    def scegli(self, cosa):
        self.chiudi()
        QTimer.singleShot(40, cosa)

    def fuori(self, ev=None):
        self.chiudi()

    def hideEvent(self, evento):
        if self.top is self:
            self._watch_timer.stop()
            self.top = None
            callback, self.al_chiudere = self.al_chiudere, None
            self.chiusa = (self.chi, time.time())
            self.chi = None
            if callback:
                QTimer.singleShot(0, callback)
        super().hideEvent(evento)

    def chiudi(self):
        if not self.isVisible():
            return
        self._watch_timer.stop()
        self.top = None
        callback, self.al_chiudere = self.al_chiudere, None
        self.chiusa = (self.chi, time.time())
        self.chi = None
        self.hide()
        if callback:
            callback()


