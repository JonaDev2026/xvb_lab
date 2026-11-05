import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from core.config import scrivi_config
from core.log import configura_logging
from core.media import e_media
from core.playlists import e_una_lista
from core.single_instance import PORTA, porta_unica
from ui.main_window import MainWindow


def argomenti_avvio(argv):
    nuova_istanza = "--nuova-istanza" in argv
    argomenti = [os.path.abspath(voce) for voce in argv if voce != "--nuova-istanza"]
    return argomenti, nuova_istanza


def percorso_istanza(nuova_istanza):
    if not nuova_istanza:
        return PORTA
    return os.path.join(
        os.path.dirname(PORTA),
        "xvb-lab-%d.sock" % os.getpid())


def main():
    configura_logging()
    logger = logging.getLogger("xvb")
    app = QApplication([sys.argv[0]])
    app.setApplicationName("XVB")
    argomenti, nuova_istanza = argomenti_avvio(sys.argv[1:])
    server = porta_unica(argomenti, percorso_istanza(nuova_istanza))
    if server is None:
        logger.info("Richiesta inoltrata a un'istanza XVB già attiva")
        print("XVB è già in esecuzione: richiesta di attivazione inviata.", flush=True)
        return 0
    try:
        finestra = MainWindow()
    except Exception as errore:
        logger.exception("Errore durante la creazione della finestra principale")
        QMessageBox.critical(
            None, "XVB - Errore di avvio",
            "Impossibile aprire la finestra principale.\n\n%s\n\n"
            "Dettagli: ~/.local/state/xvb/xvb.log" % errore)
        server.close()
        return 1
    server.files.connect(finestra.apri_da_fuori)
    server.raise_window.connect(lambda: (
        finestra.showNormal(), finestra.raise_(), finestra.activateWindow()))
    server.start()
    lista = None
    if (len(argomenti) == 1 and os.path.isfile(argomenti[0])
            and not e_media(argomenti[0]) and e_una_lista(argomenti[0])):
        lista = argomenti[0]
    if lista:
        archivio = finestra.sessione.config.setdefault("liste", [])
        if lista not in archivio:
            archivio.append(lista)
            scrivi_config(finestra.sessione.config)
        finestra.ricarica_liste(scegli=lista, forza=False)
    elif argomenti:
        QTimer.singleShot(300, lambda: finestra.apri_da_fuori(argomenti))
    finestra.show()
    risultato = app.exec()
    server.close()
    return risultato


if __name__ == "__main__":
    raise SystemExit(main())
