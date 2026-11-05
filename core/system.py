import configparser
import os
import re
import shlex
import subprocess
from pathlib import Path


def font_desktop_sistema():
    comandi = (
        ["gsettings", "get", "org.gnome.desktop.interface", "font-name"],
        ["gsettings", "get", "org.cinnamon.desktop.interface", "font-name"],
        ["xfconf-query", "-c", "xsettings", "-p", "/Gtk/FontName"],
    )
    for comando in comandi:
        try:
            valore = subprocess.check_output(
                comando, text=True, stderr=subprocess.DEVNULL, timeout=2
            ).strip()
            parti = shlex.split(valore)
            if not parti:
                continue
            if re.fullmatch(r"\d+(?:\.\d+)?", parti[-1]):
                parti.pop()
            stili = []
            while parti and parti[-1].lower() in (
                "italic", "oblique", "bold", "regular", "book", "light", "medium"
            ):
                stili.insert(0, parti.pop().lower())
            if parti:
                famiglia = " ".join(parti).strip()
                stile = "italic" if any(x in ("italic", "oblique") for x in stili) else "normal"
                peso = "bold" if "bold" in stili else "normal"
                return famiglia, stile, peso
        except Exception:
            continue
    try:
        configurazione = configparser.ConfigParser()
        configurazione.read(str(Path.home() / ".config" / "kdeglobals"), encoding="utf-8")
        parti = configurazione.get("General", "font", fallback="").split(",")
        if parti and parti[0].strip():
            stile_testo = parti[1].lower() if len(parti) > 1 else ""
            stile = "italic" if "italic" in stile_testo or "oblique" in stile_testo else "normal"
            peso = "bold" if "bold" in stile_testo else "normal"
            return parti[0].strip(), stile, peso
    except Exception:
        pass
    return None, "normal", "normal"

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_DIR = os.path.join(QUI, "fonts")
_FONT_STATIC_DIR = os.path.join(_FONT_DIR, "static")
CARATTERE = None
STILE_CARATTERE = "normal"
NOME_PX = 17
SOTTO_PX = 15


def percorso_google_sans(peso="Regular", corsivo=False):
    suffisso = "Italic" if corsivo else ""
    nome = "GoogleSans-" + peso + suffisso + ".ttf"
    percorso = os.path.join(_FONT_STATIC_DIR, nome)
    if os.path.isfile(percorso):
        return percorso
    nome = "GoogleSans_17pt-" + peso + suffisso + ".ttf"
    percorso = os.path.join(_FONT_STATIC_DIR, nome)
    return percorso if os.path.isfile(percorso) else None
