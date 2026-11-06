import json
import os

CASA = os.path.expanduser("~")
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME_APP = "xvb5"
CONFIG_DIR = os.path.join(CASA, ".config", NOME_APP)
CACHE_DIR = os.path.join(CASA, ".cache", NOME_APP)
DATA_DIR = os.path.join(CASA, ".local", "share", NOME_APP)
CONFIG = os.path.join(CONFIG_DIR, "xvb5.json")
CARTELLE_LISTE = (os.path.join(DATA_DIR, "playlists"),)
CARTELLE_VECCHIE = (os.path.join(DATA_DIR, "lists"),)
REGISTRAZIONI = os.path.join(DATA_DIR, "registrazioni")
PORTA = os.path.join(CACHE_DIR, "xvb5.sock")


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
