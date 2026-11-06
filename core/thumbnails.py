import hashlib
import io
import os
import subprocess

from .config import CACHE_DIR
from .media import AUDIO

CACHE_ANTEPRIME = os.path.join(CACHE_DIR, "anteprime")
LOGO_L, LOGO_A = 72, 56

try:
    from PIL import Image
    HA_PIL = True
except ImportError:
    HA_PIL = False


def anteprima_di(percorso):
    cartella, base = os.path.split(percorso)
    radice = os.path.splitext(base)[0]
    audio = os.path.splitext(percorso)[1][1:].lower() in AUDIO
    if not audio:
        nomi = ([radice + estensione for estensione in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")] +
                [nome + estensione for nome in ("poster", "folder", "cover")
                 for estensione in (".jpg", ".jpeg", ".png")])
    else:
        nomi = ([nome + estensione for nome in ("cover", "folder")
                 for estensione in (".jpg", ".jpeg", ".png")] +
                [radice + estensione for estensione in (".jpg", ".jpeg", ".png")])
    immagine = next((os.path.join(cartella, nome) for nome in nomi
                     if os.path.isfile(os.path.join(cartella, nome))), None)
    sorgente = immagine or percorso
    try:
        modifica = os.path.getmtime(sorgente)
    except OSError:
        return None
    os.makedirs(CACHE_ANTEPRIME, exist_ok=True)
    fuori = os.path.join(
        CACHE_ANTEPRIME,
        hashlib.md5(("%s|%s" % (sorgente, modifica)).encode()).hexdigest() + ".jpg"
    )
    if os.path.isfile(fuori):
        return fuori if os.path.getsize(fuori) else None
    dati = None
    if immagine:
        try:
            with open(immagine, "rb") as stream:
                dati = stream.read()
        except Exception:
            dati = None
    elif audio:
        from .metadata import copertina_dentro
        dati = copertina_dentro(percorso)
    try:
        if dati is not None and HA_PIL:
            imm = Image.open(io.BytesIO(dati)).convert("RGB")
            imm.thumbnail((LOGO_L * 4, LOGO_A * 4))
            imm.save(fuori, "JPEG", quality=85)
            return fuori
        if not audio:
            for secondo in ("30", "1"):
                risultato = subprocess.run(
                    ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", secondo,
                     "-i", percorso, "-frames:v", "1", "-vf", "scale=%d:-2" % (LOGO_L * 4), fuori],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20
                )
                if (risultato.returncode == 0 and os.path.isfile(fuori)
                        and os.path.getsize(fuori)):
                    return fuori
    except Exception:
        pass
    try:
        open(fuori, "wb").close()
    except Exception:
        pass
    return None
