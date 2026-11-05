from .traduzioni import LINGUE, TESTI, lingua_sistema

LINGUA = "en"


def imposta_lingua(codice):
    global LINGUA
    codici = dict(LINGUE)
    LINGUA = codice if codice in codici else lingua_sistema()
    return LINGUA


def lingua_corrente():
    return LINGUA


def _(testo):
    return TESTI.get(LINGUA, {}).get(testo, testo)
