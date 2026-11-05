import json
import os

CASA = os.path.expanduser("~")
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME_APP = "xvb5"
CONFIG_DIR = os.path.join(CASA, ".config", NOME_APP)
CACHE_DIR = os.path.join(CASA, ".cache", NOME_APP)
DATA_DIR = os.path.join(CASA, ".local", "share", NOME_APP)
STATE_DIR = os.path.join(CASA, ".local", "state", NOME_APP)
CONFIG = os.path.join(CONFIG_DIR, "xvb5.json")
CARTELLE_LISTE = (os.path.join(QUI, "playlists"),
                  os.path.join(DATA_DIR, "playlists"))
if not os.access(QUI, os.W_OK):
    CARTELLE_LISTE = CARTELLE_LISTE[::-1]
CARTELLE_VECCHIE = tuple(c for c in (os.path.join(QUI, "lists"),
                                     os.path.join(DATA_DIR, "lists"))
                         if os.path.isdir(c))
REGISTRAZIONI = os.path.join(CASA, "Videos", NOME_APP)
PORTA = os.path.join(
    os.environ.get("XDG_RUNTIME_DIR") or CACHE_DIR,
    "xvb5.sock")


def leggi_config():
    try:
        with open(CONFIG, encoding="utf-8") as stream:
            return json.load(stream)
    except Exception:
        return {}


def scrivi_config(dati):
    try:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8") as stream:
            json.dump(dati, stream, indent=1)
    except Exception:
        pass
