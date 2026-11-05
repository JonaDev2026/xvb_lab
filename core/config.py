import json
import os

CASA = os.path.expanduser("~")
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(CASA, ".config", "xvb", "xvb.json")
CONFIG_VECCHIO = os.path.join(CASA, ".config", "tv", "tv.json")
CARTELLE_LISTE = (os.path.join(QUI, "playlists"),
                  os.path.join(CASA, ".local", "share", "xvb", "playlists"))
if not os.access(QUI, os.W_OK):
    CARTELLE_LISTE = CARTELLE_LISTE[::-1]
CARTELLE_VECCHIE = tuple(c for c in (os.path.join(QUI, "lists"),
                                     os.path.join(CASA, ".local", "share", "xvb", "lists"))
                         if os.path.isdir(c))
REGISTRAZIONI = os.path.join(CASA, "Videos", "xvb")
PORTA = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or os.path.join(CASA, ".cache", "xvb"),
                     "xvb.sock")


def leggi_config():
    for percorso in (CONFIG, CONFIG_VECCHIO):
        try:
            with open(percorso, encoding="utf-8") as stream:
                return json.load(stream)
        except Exception:
            continue
    return {}


def scrivi_config(dati):
    try:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8") as stream:
            json.dump(dati, stream, indent=1)
    except Exception:
        pass
