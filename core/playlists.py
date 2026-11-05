import hashlib
import json
import os
import re
import threading
import time
from urllib.request import Request, urlopen

from i18n import _
from .config import CASA, CACHE_DIR, CARTELLE_LISTE, CARTELLE_VECCHIE
from .constants import UA
PREFERITI = "favorite"
PREF_IPTV = "iptv"
PREF_MUSICA = "music"
PREF_VIDEO = "video"
NOMI_URL = {}
LISTE_NASCOSTE = set()
BUFFER = (("minimal", "Minimal", 48, 16, 10, 5),
          ("low", "Low", 128, 32, 20, 10),
          ("standard", "Standard", 512, 128, 30, 15),
          ("high", "High", 1024, 256, 60, 15))
CATEGORIE_URL = (("podcast", "Podcast"), ("musica", "Music"), ("radio", "Radio"),
                 ("cam", "IP cam"), ("film", "Film"), ("video", "Video"))
CACHE_LISTE = os.path.join(CACHE_DIR, "liste")
LISTA_VECCHIA = 6 * 3600
_CACHE_PARSED_LOCK = threading.RLock()
_CACHE_PARSED_MEMORIA = {}
LOGHI = {}
CHIAVI = {}


def nome_di(dove):
    if dove in NOMI_URL:
        return NOMI_URL[dove]
    return os.path.splitext(os.path.basename(dove))[0] or dove


def e_una_lista(f):
    try:
        with open(f, "rb") as stream:
            testa = stream.read(4096).decode("utf-8", "ignore")
    except Exception:
        return False
    return "#EXTM3U" in testa or "#EXTINF" in testa


def liste_in(cartella):
    fuori = []
    try:
        for n in sorted(os.listdir(cartella)):
            f = os.path.join(cartella, n)
            if (not n.startswith(".") and os.path.isfile(f) and e_una_lista(f)
                    and os.path.abspath(f) not in LISTE_NASCOSTE):
                fuori.append(f)
    except Exception:
        pass
    return fuori


def liste_in_cartella():
    fuori = []
    for cartella in CARTELLE_LISTE + CARTELLE_VECCHIE:
        fuori += liste_in(cartella)
    return fuori


def categorie():
    fuori = []
    for cartella in CARTELLE_LISTE + CARTELLE_VECCHIE:
        try:
            nomi = sorted(os.listdir(cartella))
        except Exception:
            continue
        for n in nomi:
            f = os.path.join(cartella, n)
            if n.startswith(".") or n == "img" or not os.path.isdir(f):
                continue
            dentro = liste_in(f)
            if dentro:
                fuori.append((n, dentro))
    return fuori


def copia_lista_url(url, aggiorna=True):
    os.makedirs(CACHE_LISTE, exist_ok=True)
    f = os.path.join(CACHE_LISTE, hashlib.md5(url.encode()).hexdigest() + ".m3u")
    fresca = os.path.isfile(f) and time.time() - os.path.getmtime(f) < LISTA_VECCHIA
    if fresca and aggiorna != "forza":
        return f
    try:
        richiesta = Request(url, headers={"User-Agent": UA})
        dati = urlopen(richiesta, timeout=30).read()
        if b"#EXTINF" not in dati[:65536]:
            raise ValueError("not an m3u playlist")
        with open(f, "wb") as stream:
            stream.write(dati)
    except Exception:
        if not os.path.isfile(f):
            raise
    return f


def _percorso_lista(f, solo_cache=False):
    if re.match(r"https?://", f, re.I):
        percorso = os.path.join(CACHE_LISTE, hashlib.md5(f.encode()).hexdigest() + ".m3u")
        if not os.path.isfile(percorso):
            if solo_cache:
                return None
            percorso = copia_lista_url(f)
        return percorso
    return f if os.path.isfile(f) else None


def _cache_lista_memoria_valida(f):
    percorso = _percorso_lista(f, solo_cache=True)
    if not percorso:
        return None
    try:
        st = os.stat(percorso)
        with _CACHE_PARSED_LOCK:
            voce = _CACHE_PARSED_MEMORIA.get(f)
            if (voce and voce[0] == os.path.abspath(percorso)
                    and voce[1] == st.st_mtime_ns and voce[2] == st.st_size):
                return voce[3]
    except OSError:
        pass
    return None


def _cache_lista_valida(f):
    dati = _cache_lista_memoria_valida(f)
    if dati is not None:
        return dati
    percorso = _percorso_lista(f, solo_cache=True)
    if not percorso:
        return None
    chiave = hashlib.sha256(f.encode("utf-8", "replace")).hexdigest()
    archivio = os.path.join(CACHE_LISTE, "parsed", chiave + ".json")
    try:
        st = os.stat(percorso)
        with open(archivio, "r", encoding="utf-8") as stream:
            dati = json.load(stream)
        if (dati.get("versione") == 1 and dati.get("percorso") == os.path.abspath(percorso)
                and dati.get("mtime_ns") == st.st_mtime_ns and dati.get("dimensione") == st.st_size):
            with _CACHE_PARSED_LOCK:
                _CACHE_PARSED_MEMORIA[f] = (os.path.abspath(percorso), st.st_mtime_ns, st.st_size, dati)
            return dati
    except (OSError, ValueError, TypeError):
        return None
    return None


def _dati_lista(f, solo_cache=False):
    percorso = _percorso_lista(f, solo_cache=solo_cache)
    if not percorso:
        return {"canali": [], "categorie": {}, "loghi": {}, "chiavi": {}}
    os.makedirs(os.path.join(CACHE_LISTE, "parsed"), exist_ok=True)
    chiave = hashlib.sha256(f.encode("utf-8", "replace")).hexdigest()
    archivio = os.path.join(CACHE_LISTE, "parsed", chiave + ".json")
    with _CACHE_PARSED_LOCK:
        dati = _cache_lista_valida(f)
        if dati is not None:
            return dati
        st = os.stat(percorso)
        canali, categorie_lista, loghi, chiavi = [], {}, {}, {}
        nome = ide = logo = lic = None
        categoria = ""
        with open(percorso, encoding="utf-8", errors="ignore") as sorgente:
            for riga in sorgente:
                riga = riga.strip()
                if riga.startswith("#EXTINF"):
                    m = re.match(r'#EXTINF:[^,\"]*(?:\"[^\"]*\"[^,]*)*,(.*)$', riga)
                    nome = (m.group(1) if m else riga.split(",", 1)[-1]).strip() or _("unnamed")
                    m = re.search(r'tvg-id="([^\"]*)"', riga)
                    ide = m.group(1).strip() if m else None
                    m = re.search(r'tvg-logo="([^\"]+)"', riga)
                    logo = m.group(1).strip() if m else None
                    m = re.search(r'license-type="([^\"]*)"', riga)
                    d = re.search(r'license-details="([^\"]*)"', riga)
                    lic = d.group(1).strip() if m and d and m.group(1).strip().lower() == "clearkey" else None
                    m = re.search(r'group-title="([^\"]*)"', riga, re.I)
                    categoria = m.group(1).strip() if m else ""
                elif riga and not riga.startswith("#"):
                    canali.append([nome or riga, riga, ide or None])
                    categorie_lista[riga] = categoria
                    if logo:
                        loghi[riga] = logo
                    if lic:
                        chiavi[riga] = lic
                    nome = ide = logo = lic = None
                    categoria = ""
        dati = {"versione": 1, "percorso": os.path.abspath(percorso),
                "mtime_ns": st.st_mtime_ns, "dimensione": st.st_size,
                "canali": canali, "categorie": categorie_lista, "loghi": loghi, "chiavi": chiavi}
        temporaneo = archivio + ".tmp"
        with open(temporaneo, "w", encoding="utf-8") as stream:
            json.dump(dati, stream, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporaneo, archivio)
        _CACHE_PARSED_MEMORIA[f] = (os.path.abspath(percorso), st.st_mtime_ns, st.st_size, dati)
        return dati


def leggi_lista(f, solo_cache=False):
    dati = _dati_lista(f, solo_cache=solo_cache)
    LOGHI.update(dati.get("loghi", {}))
    CHIAVI.update(dati.get("chiavi", {}))
    return [tuple(c) for c in dati.get("canali", [])]


def _cat_vuota(d):
    return "MyPlaylist" if os.path.basename(os.path.dirname(d)) == PREFERITI else "Altri"


def nome_vista(d):
    if os.path.basename(os.path.dirname(d)) == PREFERITI:
        n = os.path.splitext(os.path.basename(d))[0]
        return {PREF_IPTV: "IPTV", PREF_MUSICA: _("Music"), PREF_VIDEO: _("Video")}.get(n, n)
    return nome_di(d)


def categorie_m3u(f, solo_cache=True):
    dati = _dati_lista(f, solo_cache=solo_cache)
    return {url: (categoria or _cat_vuota(f)) for url, categoria in dati.get("categorie", {}).items()}
