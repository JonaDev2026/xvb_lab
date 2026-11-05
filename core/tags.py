import json
import os

from .config import CASA

FILE_TAG = os.path.join(CASA, ".cache", "xvb", "tag.json")

try:
    import mutagen
    HA_TAG = True
except ImportError:
    HA_TAG = False


def leggi_tag():
    try:
        with open(FILE_TAG, encoding="utf-8") as stream:
            return json.load(stream)
    except Exception:
        return {}


def scrivi_tag(dati):
    try:
        os.makedirs(os.path.dirname(FILE_TAG), exist_ok=True)
        with open(FILE_TAG, "w", encoding="utf-8") as stream:
            json.dump(dati, stream)
    except Exception:
        pass


def tag_di(percorso, cache):
    vuoto = ("", "", "", "")
    if not HA_TAG:
        return vuoto
    try:
        modifica = os.path.getmtime(percorso)
    except OSError:
        return vuoto
    voce = cache.get(percorso)
    if voce and voce[0] == modifica and len(voce) == 5:
        return tuple(voce[1:])
    titolo, artista, album, anno = vuoto
    try:
        tag = mutagen.File(percorso, easy=True)
        if tag and tag.tags:
            prendi = lambda chiave: str((tag.tags.get(chiave) or [""])[0]).strip()
            titolo, artista, album = prendi("title"), prendi("artist"), prendi("album")
            data = prendi("date")
            anno = data[:4] if data[:4].isdigit() else ""
    except Exception:
        pass
    cache[percorso] = [modifica, titolo, artista, album, anno]
    return titolo, artista, album, anno
