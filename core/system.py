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
