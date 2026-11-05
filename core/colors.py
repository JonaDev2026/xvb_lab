import colorsys
import hashlib
import json
import os
import subprocess
from urllib.request import Request, urlopen

from .config import CASA, QUI
from .constants import UA

CACHE_LOGHI = os.path.join(CASA, ".cache", "xvb", "loghi")
FILE_COLORI = os.path.join(CASA, ".cache", "xvb", "colori.json")
COLORI_VERSIONE = 4

try:
    from PIL import Image
    HA_PIL = True
except ImportError:
    HA_PIL = False


def svg_in_png(dati):
    if b"<svg" not in dati[:4096].lower():
        return dati
    try:
        risultato = subprocess.run(["rsvg-convert", "-w", "256"], input=dati,
                                   capture_output=True, timeout=15)
        if risultato.returncode == 0 and risultato.stdout:
            return risultato.stdout
    except Exception:
        pass
    try:
        import cairosvg
        return cairosvg.svg2png(bytestring=dati, output_width=256)
    except Exception:
        return dati


def schiarisci(colore, minimo=0.80):
    try:
        r, g, b = (int(colore[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    except (ValueError, TypeError, IndexError):
        return colore
    h, luce, saturazione = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, max(luce, minimo), saturazione)
    return "#%02x%02x%02x" % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def colore_dal_logo(url_logo):
    if not HA_PIL:
        return None
    os.makedirs(CACHE_LOGHI, exist_ok=True)
    percorso = os.path.join(CACHE_LOGHI, hashlib.md5(url_logo.encode()).hexdigest())
    if not os.path.isfile(percorso) or os.path.getsize(percorso) == 0:
        richiesta = Request(url_logo, headers={"User-Agent": UA})
        dati = svg_in_png(urlopen(richiesta, timeout=10).read())
        with open(percorso, "wb") as stream:
            stream.write(dati)
    try:
        immagine = Image.open(percorso).convert("RGBA")
    except Exception:
        os.remove(percorso)
        raise
    immagine.thumbnail((48, 48))
    secchi = {}
    for r, g, b, a in immagine.getdata():
        if a < 128:
            continue
        h, luce, saturazione = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        if saturazione < 0.35 or luce < 0.12 or luce > 0.92:
            continue
        chiave = int(h * 12) % 12
        totale = secchi.setdefault(chiave, [0, 0.0, 0.0, 0.0])
        totale[0] += 1
        totale[1] += h
        totale[2] += luce
        totale[3] += saturazione
    if not secchi:
        return None
    n, h, luce, saturazione = max(secchi.values(), key=lambda voce: voce[0])
    h, luce, saturazione = h / n, luce / n, saturazione / n
    luce = min(0.72, max(0.55, luce))
    saturazione = max(0.75, saturazione)
    if 0.55 <= h <= 0.75:
        luce = max(luce, 0.63)
    r, g, b = colorsys.hls_to_rgb(h, luce, saturazione)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def leggi_colori():
    try:
        with open(FILE_COLORI, encoding="utf-8") as stream:
            dati = json.load(stream)
        if dati.get("_v") != COLORI_VERSIONE:
            return {}
        dati.pop("_v", None)
        return dati
    except Exception:
        return {}


def scrivi_colori(dati):
    try:
        os.makedirs(os.path.dirname(FILE_COLORI), exist_ok=True)
        with open(FILE_COLORI, "w", encoding="utf-8") as stream:
            json.dump(dict(dati, _v=COLORI_VERSIONE), stream)
    except Exception:
        pass


def immagine_lista(dove):
    nomi = (["m3u"] if dove else []) + ["default"]
    for nome in nomi:
        for estensione in (".png", ".jpg", ".jpeg", ".gif"):
            percorso = os.path.join(QUI, "icone", nome + estensione)
            if os.path.isfile(percorso):
                return percorso
    return None


def colore_sfondo_guida(hex_colore, bg_hex="#121212", alfa=0.40):
    try:
        h_c = hex_colore.lstrip("#")
        r1, g1, b1 = int(h_c[0:2], 16), int(h_c[2:4], 16), int(h_c[4:6], 16)
        bg_c = bg_hex.lstrip("#")
        r2, g2, b2 = int(bg_c[0:2], 16), int(bg_c[2:4], 16), int(bg_c[4:6], 16)
        rf = int(r1 * alfa + r2 * (1.0 - alfa))
        gf = int(g1 * alfa + g2 * (1.0 - alfa))
        bf = int(b1 * alfa + b2 * (1.0 - alfa))
        return "#%02x%02x%02x" % (rf, gf, bf)
    except Exception:
        return "#252030"
