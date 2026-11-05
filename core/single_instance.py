import os
import socket
import threading

from PySide6.QtCore import QObject, Signal

from core.config import PORTA


class ServerUnico(QObject):
    files = Signal(object)
    raise_window = Signal()

    def __init__(self, percorso=PORTA):
        super().__init__()
        self.percorso = percorso
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        try:
            os.remove(percorso)
        except OSError:
            pass
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(percorso)
        self.server.listen(4)
        self._attivo = True
        self._thread = None

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._ascolta, daemon=True)
            self._thread.start()

    def _ascolta(self):
        while self._attivo:
            try:
                connessione, _indirizzo = self.server.accept()
            except OSError:
                return
            if not self._attivo:
                connessione.close()
                return
            with connessione:
                parti = []
                while True:
                    try:
                        blocco = connessione.recv(65536)
                    except OSError:
                        break
                    if not blocco:
                        break
                    parti.append(blocco)
            dati = b"".join(parti)
            percorsi = [voce for voce in dati.decode("utf-8", "replace").split("\n") if voce]
            if percorsi:
                self.files.emit(percorsi)
            else:
                self.raise_window.emit()

    def close(self):
        self._attivo = False
        try:
            risveglio = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            risveglio.settimeout(0.2)
            risveglio.connect(self.percorso)
            risveglio.close()
        except OSError:
            pass
        self.server.close()
        if self._thread is not None:
            self._thread.join(1)
        try:
            os.remove(self.percorso)
        except OSError:
            pass


def porta_unica(argomenti, percorso=PORTA):
    def inoltra():
        connessione = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connessione.settimeout(2)
        try:
            connessione.connect(percorso)
            dati = "\n".join(os.path.abspath(voce) for voce in argomenti if voce)
            if dati:
                connessione.sendall(dati.encode("utf-8"))
            return True
        except OSError:
            return False
        finally:
            connessione.close()

    if inoltra():
        return None
    try:
        return ServerUnico(percorso)
    except OSError:
        if inoltra():
            return None
        raise
