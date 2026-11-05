import logging
import os
import re
import sys
import threading
from logging.handlers import RotatingFileHandler

from .config import CASA
from .constants import VERSIONE


_XVB_LOGGER = logging.getLogger("xvb")


class _XVBFiltroSicurezza(logging.Filter):
    _parametri = re.compile(
        r"(?i)(password|passwd|username|user|token|"
        r"api[_-]?key|authorization|secret)=([^&\\s]+)"
    )
    _autenticazione = __import__("re").compile(
        r"(?i)(https?://)[^/@\\s:]+:[^/@\\s]+@"
    )

    def filter(self, record):
        try:
            testo = record.getMessage()
            testo = self._parametri.sub(r"\\1=[REDACTED]", testo)
            testo = self._autenticazione.sub(r"\\1[REDACTED]@", testo)
            record.msg = testo
            record.args = ()
        except Exception:
            pass
        return True


def _xvb_eccezione(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    _XVB_LOGGER.critical(
        "Eccezione non gestita",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def _xvb_eccezione_thread(args):
    _XVB_LOGGER.error(
        "Eccezione non gestita nel thread %s",
        getattr(args.thread, "name", "sconosciuto"),
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )


def _xvb_eccezione_gui(exc_type, exc_value, exc_traceback):
    _XVB_LOGGER.error(
        "Errore in un callback GUI",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def configura_logging():
    if _XVB_LOGGER.handlers:
        return
    _XVB_LOGGER.setLevel(logging.INFO)
    _XVB_LOGGER.propagate = False
    filtro = _XVBFiltroSicurezza()
    percorsi = (
        os.path.join(CASA, ".local", "state", "xvb"),
        os.path.join(CASA, ".cache", "xvb"),
    )
    for cartella in percorsi:
        try:
            os.makedirs(cartella, exist_ok=True)
            percorso = os.path.join(cartella, "xvb.log")
            gestore = RotatingFileHandler(
                percorso,
                maxBytes=2 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
            gestore.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s"
            ))
            gestore.addFilter(filtro)
            _XVB_LOGGER.addHandler(gestore)
            _XVB_LOGGER.info("XVB %s avviato", VERSIONE)
            sys.excepthook = _xvb_eccezione
            if hasattr(threading, "excepthook"):
                threading.excepthook = _xvb_eccezione_thread
            return
        except OSError:
            continue
    gestore = logging.StreamHandler(sys.stderr)
    gestore.addFilter(filtro)
    _XVB_LOGGER.addHandler(gestore)
    _XVB_LOGGER.error("Impossibile creare il file di log su disco")
