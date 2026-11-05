import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from core.config import CASA

PORTA = os.path.join(
    os.environ.get("XDG_RUNTIME_DIR") or os.path.join(CASA, ".cache", "xvb"),
    "xvb.sock")


class ServerUnico(QObject):
    files = Signal(object)
    raise_window = Signal()

    def __init__(self, percorso=PORTA):
        super().__init__()
        self.percorso = percorso
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        QLocalServer.removeServer(percorso)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._nuova_connessione)
        if not self.server.listen(percorso):
            raise OSError(self.server.errorString())
        self._buffer = {}

    def _nuova_connessione(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self._buffer[socket] = bytearray()
            socket.readyRead.connect(lambda s=socket: self._leggi(s))
            socket.disconnected.connect(lambda s=socket: self._disconnesso(s))
            if socket.bytesAvailable():
                self._leggi(socket)

    def _leggi(self, socket):
        if socket in self._buffer:
            self._buffer[socket].extend(bytes(socket.readAll()))

    def _disconnesso(self, socket):
        dati = bytes(self._buffer.pop(socket, b""))
        percorsi = [voce for voce in dati.decode("utf-8", "replace").split("\n") if voce]
        if percorsi:
            self.files.emit(percorsi)
        else:
            self.raise_window.emit()
        socket.deleteLater()

    def close(self):
        self.server.close()
        QLocalServer.removeServer(self.percorso)


def porta_unica(argomenti, percorso=PORTA):
    def inoltra():
        socket = QLocalSocket()
        socket.connectToServer(percorso)
        if not socket.waitForConnected(2000):
            return False
        dati = "\n".join(os.path.abspath(voce) for voce in argomenti if voce)
        if dati:
            socket.write(dati.encode("utf-8"))
            socket.flush()
            if not socket.waitForBytesWritten(2000):
                socket.abort()
                return False
        socket.disconnectFromServer()
        if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            socket.waitForDisconnected(2000)
        return True

    if inoltra():
        return None
    try:
        return ServerUnico(percorso)
    except OSError:
        if inoltra():
            return None
        raise
