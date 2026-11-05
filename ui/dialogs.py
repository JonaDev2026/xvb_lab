from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget, QScrollArea, QMenu
)


class Finestrella(QDialog):
    def __init__(self, root, titolo, corpo, chiedi=None, valore="",
                 ok=None, annulla=None, larga=420, domanda=False,
                 maschera=False, colori=None):
        super().__init__(root)
        c = colori or {}
        pannello = c.get("pannello", "#1b1b1f")
        cerca = c.get("cerca", "#252529")
        testo = c.get("testo", "#f2f2f2")
        grigio = c.get("grigio", "#92929a")
        accento = c.get("accento", "#a78bfa")
        scelto = c.get("scelto", "#393044")
        self.setWindowTitle(titolo)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedWidth(larga)
        self.risposta = None
        self._colori = (pannello, cerca, testo, grigio, accento, scelto)
        self.setStyleSheet("QDialog{background:%s;color:%s}" % (pannello, testo))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(8)
        contenuto = QWidget(self)
        corpo(contenuto)
        layout.addWidget(contenuto)
        self.casella = None
        if chiedi is not None:
            etichetta = QLabel(chiedi, self)
            etichetta.setStyleSheet("color:%s" % grigio)
            layout.addWidget(etichetta)
            self.casella = QLineEdit(self)
            self.casella.setText(valore)
            self.casella.setEchoMode(QLineEdit.Password if maschera else QLineEdit.Normal)
            self.casella.selectAll()
            self.casella.setStyleSheet(
                "QLineEdit{background:%s;color:%s;border:1px solid %s;padding:7px}" %
                (cerca, testo, scelto))
            layout.addWidget(self.casella)
        riga = QHBoxLayout()
        riga.addStretch(1)
        def bottone(etichetta, callback, primario=False):
            b = QPushButton(etichetta, self)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{background:%s;color:%s;border:0;padding:6px 16px}"
                "QPushButton:hover{background:%s}" %
                ((c.get("in_onda", accento) if primario else cerca),
                 (c.get("testo_onda", "#ffffff") if primario else testo), scelto))
            b.clicked.connect(callback)
            riga.addWidget(b)
            return b
        bottone(ok or "OK", self.va_bene, True)
        if chiedi is not None or domanda:
            bottone(annulla or "Cancel", self.lascia)
        layout.addLayout(riga)
        self.setMinimumWidth(max(360, larga))
        self.adjustSize()
        if self.casella:
            self.casella.setFocus()
        QTimer.singleShot(0, self._centra)

    def _centra(self):
        parent = self.parentWidget()
        if parent:
            self.move(parent.frameGeometry().center() - self.rect().center())

    def va_bene(self):
        self.risposta = self.casella.text() if self.casella is not None else True
        self.accept()

    def lascia(self):
        self.risposta = None
        self.reject()


class Tendina:
    ALTA = 30

    def __init__(self, root, colori=None):
        self.root = root
        self.menu = None
        self.al_chiudere = None
        self.chi = None
        self.altrove = None
        self.colori = colori or {}

    def aperta(self):
        return self.menu is not None

    def apri(self, x, y, voci, sopra=False, destra=False,
             al_chiudere=None, chi=None, altrove=None):
        self.chiudi()
        self.al_chiudere, self.chi, self.altrove = al_chiudere, chi, altrove
        pannello = self.colori.get("pannello", "#1b1b1f")
        testo = self.colori.get("testo", "#f2f2f2")
        grigio = self.colori.get("grigio", "#92929a")
        accento = self.colori.get("accento", "#a78bfa")
        scelto = self.colori.get("scelto", "#393044")
        menu = QMenu(self.root)
        menu.setStyleSheet(
            "QMenu{background:%s;color:%s;border:1px solid %s;padding:3px}"
            "QMenu::item{padding:7px 18px 7px 12px;min-height:16px}"
            "QMenu::item:selected{background:%s;color:#fff}"
            "QMenu::item:disabled{color:%s}"
            "QMenu::separator{height:1px;background:%s;margin:4px 9px}" %
            (pannello, testo, scelto, scelto, grigio, scelto))
        def aggiungi(lista):
            for voce in lista:
                if voce is None:
                    menu.addSeparator()
                elif voce and voce[0] is SCORRE:
                    _, elementi, righe = voce
                    sotto = menu.addMenu("")
                    sotto.setTitle("More")
                    for elemento in elementi:
                        if elemento is None:
                            sotto.addSeparator()
                        else:
                            et, azione = elemento
                            spunta = et.startswith("*  ")
                            et = et[3:] if et[:3] in ("*  ", "   ") else et
                            a = sotto.addAction(("✓  " if spunta else "   ") + et)
                            a.setEnabled(bool(azione))
                            if azione:
                                a.triggered.connect(azione)
                else:
                    et, azione = voce
                    spunta = et.startswith("*  ")
                    et = et[3:] if et[:3] in ("*  ", "   ") else et
                    a = menu.addAction(("✓  " if spunta else "") + et)
                    a.setEnabled(bool(azione))
                    if azione:
                        a.triggered.connect(azione)
        aggiungi(voci)
        menu.aboutToHide.connect(self._chiusa)
        self.menu = menu
        menu.ensurePolished()
        pos = QPoint(x, y)
        if sopra:
            pos.setY(y - menu.sizeHint().height())
        if destra:
            pos.setX(x - menu.sizeHint().width())
        menu.popup(pos)

    def _chiusa(self):
        self.menu = None
        callback, self.al_chiudere = self.al_chiudere, None
        self.chi = None
        if callback:
            callback()

    def scegli(self, cosa):
        self.chiudi()
        QTimer.singleShot(40, cosa)

    def chiudi(self):
        menu, self.menu = self.menu, None
        if menu:
            menu.close()
            menu.deleteLater()
        callback, self.al_chiudere = self.al_chiudere, None
        if callback:
            callback()


SCORRE = object()
