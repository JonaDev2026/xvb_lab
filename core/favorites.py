import os

from .config import CARTELLE_LISTE
from .playlists import CHIAVI, categorie_m3u, leggi_lista

PREFERITI = "favorite"
PREF_IPTV = "iptv"
PREF_MUSICA = "music"
PREF_VIDEO = "video"


def cartella_liste_in_uso():
    for cartella in CARTELLE_LISTE:
        try:
            if any(not n.startswith(".") for n in os.listdir(cartella)):
                return cartella
        except Exception:
            continue
    return CARTELLE_LISTE[0]


def file_preferiti(tipo=PREF_IPTV):
    nome = tipo
    for cartella in CARTELLE_LISTE:
        percorso = os.path.join(cartella, PREFERITI, nome + ".m3u")
        if os.path.isfile(percorso):
            return percorso
        vecchio = os.path.join(cartella, PREFERITI, PREFERITI + ".m3u")
        if tipo == PREF_IPTV and os.path.isfile(vecchio):
            try:
                os.rename(vecchio, percorso)
                return percorso
            except Exception:
                return vecchio
    return os.path.join(cartella_liste_in_uso(), PREFERITI, nome + ".m3u")


def leggi_preferiti_cat(tipo=PREF_IPTV):
    percorso = file_preferiti(tipo)
    if not os.path.isfile(percorso):
        return []
    try:
        canali = leggi_lista(percorso)
        categorie = categorie_m3u(percorso)
    except Exception:
        return []
    return [(nome, url, ide, categorie.get(url, "MyPlaylist")) for nome, url, ide in canali]


def leggi_preferiti(tipo=PREF_IPTV):
    percorso = file_preferiti(tipo)
    if not os.path.isfile(percorso):
        return []
    try:
        return leggi_lista(percorso)
    except Exception:
        return []


def scrivi_preferiti(canali, tipo=PREF_IPTV):
    percorso = file_preferiti(tipo)
    if not canali:
        try:
            os.remove(percorso)
        except Exception:
            pass
        try:
            os.rmdir(os.path.dirname(percorso))
        except Exception:
            pass
        return
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    with open(percorso, "w", encoding="utf-8") as stream:
        stream.write("#EXTM3U\n")
        for voce in canali:
            nome, url, ide = voce[0], voce[1], voce[2]
            categoria = voce[3] if len(voce) > 3 else ""
            licenza = (' license-type="clearkey" license-details="%s"' % CHIAVI[url]
                       if url in CHIAVI else "")
            gruppo = (' group-title="%s"' % categoria.replace('"', "'")) if categoria else ""
            stream.write("#EXTINF:-1%s,%s\n%s\n" % (
                (' tvg-id="%s"' % ide if ide else "") + licenza + gruppo, nome, url))
