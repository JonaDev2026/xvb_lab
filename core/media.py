import os
import re
import subprocess
from urllib.parse import urlparse

MEDIA = ("mkv", "mp4", "avi", "mov", "webm", "ts", "m2ts", "mpg", "mpeg", "wmv", "flv",
         "ogv", "m4v", "mp3", "flac", "ogg", "opus", "m4a", "aac", "wav", "wma", "ape", "mka")
AUDIO = ("mp3", "flac", "ogg", "opus", "m4a", "aac", "wav", "wma", "ape", "mka")
PREF_IPTV = "iptv"
PREF_MUSICA = "music"
PREF_VIDEO = "video"
_DURATE = {}


def e_media(f):
    return os.path.splitext(f)[1][1:].lower() in MEDIA


def nome_url(u):
    return os.path.basename(urlparse(u).path.rstrip("/")) or urlparse(u).netloc or u


def titolo_url(u):
    pezzi = [x for x in urlparse(u).path.split("/") if x]
    n = pezzi[-1] if pezzi else ""
    m = re.match(r"(.*)\.([A-Za-z0-9]+)$", n)
    if m and (m.group(2).lower() in MEDIA or m.group(2).lower() in ("m3u8", "m3u", "mpd", "ism")):
        n = m.group(1)
    if not n and len(pezzi) > 1:
        n = re.sub(r"\.[A-Za-z0-9]+$", "", pezzi[-2])
    return re.sub(r"[_.-]+", " ", n).strip() or urlparse(u).netloc or u


def tipo_url(u):
    p, sito = urlparse(u).path, urlparse(u).netloc
    m = re.search(r"\.([A-Za-z0-9]+)$", p)
    est = m.group(1).lower() if m else ""
    if est in AUDIO:
        cosa = "Audio · " + est.upper()
    elif est in MEDIA:
        cosa = "Video · " + est.upper()
    elif est in ("m3u8", "m3u"):
        cosa = "Stream HLS"
    elif est == "mpd":
        cosa = "Stream DASH"
    else:
        cosa = "Stream"
    return cosa + (" · " + sito if sito else "")


def e_media_url(u):
    return bool(re.match(r"https?://", u or "", re.I)) and e_media(urlparse(u).path)


def media_in(cartella):
    fuori = []
    try:
        for dove, sotto, nomi in os.walk(cartella):
            sotto[:] = sorted((d for d in sotto if not d.startswith(".")), key=str.lower)
            for n in sorted(nomi, key=str.lower):
                if not n.startswith(".") and e_media(n):
                    fuori.append((os.path.splitext(n)[0], os.path.join(dove, n), None))
    except Exception:
        pass
    return fuori


def ore_min_sec(secondi):
    secondi = int(max(0, secondi))
    ore, resto = divmod(secondi, 3600)
    return ("%d:%02d:%02d" % (ore, resto // 60, resto % 60) if ore
            else "%02d:%02d" % (resto // 60, resto % 60))


def durata_di(f):
    try:
        k = (f, os.path.getmtime(f))
    except OSError:
        return None
    if k not in _DURATE:
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1", f],
                               capture_output=True, text=True, timeout=15)
            _DURATE[k] = float(r.stdout.strip())
        except Exception:
            _DURATE[k] = None
    return _DURATE[k]


def tipo_preferiti(url):
    if not (os.path.isabs(url) and e_media(url)):
        return PREF_IPTV
    return PREF_MUSICA if os.path.splitext(url)[1][1:].lower() in AUDIO else PREF_VIDEO
