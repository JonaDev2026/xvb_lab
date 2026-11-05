from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QBrush, QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView

from .list import _pixmap


_DATA = Qt.UserRole + 51


class Sidebar(QTreeWidget):
    selected = Signal(str)
    folderChanged = Signal(str, bool)
    removeRequested = Signal(str)

    def __init__(self, parent=None, colori=None):
        super().__init__(parent)
        c = colori or {}
        self._progressivo = 0
        self.pannello = c.get("pannello", "#1c1b22")
        self.testo = c.get("testo", "#e0e0e0")
        self.grigio = c.get("grigio", "#9e9e9e")
        self.scelto = c.get("scelto", "#0071e3")
        self.zebra = c.get("zebra", "#2b2a33")
        self.setHeaderHidden(True)
        self.setColumnCount(2)
        self.setColumnWidth(0, 170)
        self.setColumnWidth(1, 26)
        self.setIndentation(14)
        self.setIconSize(QSize(24, 24))
        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setExpandsOnDoubleClick(False)
        self.setStyleSheet(
            "QTreeWidget{background:%s;color:%s;border:0;outline:0}"
            "QTreeWidget::item{height:32px;padding:2px}"
            "QTreeWidget::item:selected{background:%s;color:#ffffff}"
            "QTreeWidget::branch{background:%s}"
            "QTreeWidget::branch:has-siblings:!adjoins-item{border-image:none}"
            "QTreeWidget::branch:has-siblings:adjoins-item{border-image:none}"
            "QTreeWidget::branch:!has-children:!has-siblings{border-image:none}" %
            (self.pannello, self.testo, self.scelto, self.pannello))
        self.itemClicked.connect(self._clic)
        self.itemExpanded.connect(lambda item: self._aperto(item, True))
        self.itemCollapsed.connect(lambda item: self._aperto(item, False))
        self.itemDoubleClicked.connect(self._doppio)

    def insert(self, parent, index="end", iid=None, text="", image=None,
               values=(), open=False, tags=()):
        if iid is None:
            iid = str(self._progressivo)
            self._progressivo += 1
        item = QTreeWidgetItem()
        item.setText(0, text)
        pix = _pixmap(image)
        if pix is not None:
            item.setIcon(0, QIcon(pix))
        if values:
            item.setText(1, str(values[0]))
        item.setData(0, _DATA, {
            "iid": iid, "text": text, "image": image,
            "values": tuple(values), "tags": tuple(tags), "open": bool(open)
        })
        if parent is None or parent == "":
            self.insertTopLevelItem(self.topLevelItemCount() if index == "end" else int(index), item)
        else:
            padre = parent if isinstance(parent, QTreeWidgetItem) else self.item_by_id(parent)
            if padre is None:
                raise KeyError(parent)
            padre.addChild(item)
        item.setExpanded(bool(open))
        if "usata" in tags:
            item.setForeground(0, QBrush(QColor(self.testo)))
        if "sotto" in tags:
            item.setBackground(0, QBrush(QColor(self.zebra)))
        if iid is not None:
            item.setData(0, Qt.UserRole, iid)
        return iid

    def item_by_id(self, iid):
        for item in self._tutti():
            if item.data(0, Qt.UserRole) == iid:
                return item
        return None

    def _tutti(self):
        risultato = []
        def visita(padre):
            for i in range(padre.childCount()):
                item = padre.child(i)
                risultato.append(item)
                visita(item)
        visita(self.invisibleRootItem())
        return risultato

    def get_children(self, parent=None):
        if parent is None or parent == "":
            padre = self.invisibleRootItem()
        else:
            padre = parent if isinstance(parent, QTreeWidgetItem) else self.item_by_id(parent)
        return tuple(padre.child(i).data(0, Qt.UserRole) for i in range(padre.childCount())) if padre else ()

    def exists(self, iid):
        return self.item_by_id(iid) is not None

    def delete(self, *items):
        if not items:
            self.clear()
            return
        for value in items:
            item = value if isinstance(value, QTreeWidgetItem) else self.item_by_id(value)
            if item is None:
                continue
            parent = item.parent()
            if parent is None:
                index = self.indexOfTopLevelItem(item)
                if index >= 0:
                    self.takeTopLevelItem(index)
            else:
                parent.removeChild(item)

    def move(self, iid, parent, index="end"):
        item = self.item_by_id(iid)
        if item is None:
            return
        old = item.parent()
        if old is None:
            old_index = self.indexOfTopLevelItem(item)
            item = self.takeTopLevelItem(old_index)
        else:
            old.removeChild(item)
        if parent is None or parent == "":
            pos = self.topLevelItemCount() if index == "end" else int(index)
            self.insertTopLevelItem(pos, item)
        else:
            nuovo = parent if isinstance(parent, QTreeWidgetItem) else self.item_by_id(parent)
            nuovo.addChild(item)

    def item(self, iid, option=None, **kw):
        item = iid if isinstance(iid, QTreeWidgetItem) else self.item_by_id(iid)
        if item is None:
            raise KeyError(iid)
        dati = item.data(0, _DATA) or {}
        if option:
            return dati.get(option)
        if kw:
            dati.update(kw)
            item.setData(0, _DATA, dati)
            if "text" in kw:
                item.setText(0, kw["text"])
            if "values" in kw:
                valori = kw["values"]
                item.setText(1, str(valori[0]) if valori else "")
            if "image" in kw:
                pix = _pixmap(kw["image"])
                item.setIcon(0, QIcon(pix) if pix is not None else QIcon())
            if "open" in kw:
                item.setExpanded(bool(kw["open"]))
        return dict(dati)

    def selection(self):
        return tuple(item.data(0, Qt.UserRole) for item in self.selectedItems())

    def selection_set(self, iid):
        item = iid if isinstance(iid, QTreeWidgetItem) else self.item_by_id(iid)
        self.setCurrentItem(item)

    def selection_remove(self, iid):
        item = iid if isinstance(iid, QTreeWidgetItem) else self.item_by_id(iid)
        if item is not None and item.isSelected():
            self.setCurrentItem(None)

    def _clic(self, item, colonna):
        iid = item.data(0, Qt.UserRole)
        if iid is not None:
            self.selected.emit(str(iid))
        if colonna == 1 and item.text(1):
            self.removeRequested.emit(str(iid))

    def _doppio(self, item, colonna):
        if item.childCount():
            item.setExpanded(not item.isExpanded())

    def _aperto(self, item, aperto):
        dati = item.data(0, _DATA) or {}
        dati["open"] = aperto
        item.setData(0, _DATA, dati)
        iid = item.data(0, Qt.UserRole)
        if iid is not None:
            self.folderChanged.emit(str(iid), aperto)

    def scroll_to(self, iid):
        item = self.item_by_id(iid)
        if item is not None:
            self.scrollToItem(item)
