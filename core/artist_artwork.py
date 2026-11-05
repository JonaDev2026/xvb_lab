import hashlib
import json
import os
import threading
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.metadata import dal_percorso
from core.tags import tag_di
from core.media import AUDIO
from core.constants import UA

CACHE_ARTISTI = os.path.join(os.path.expanduser("~"), ".cache", "xvb5", "artisti")
CACHE_ARTISTI_INDEX = os.path.join(CACHE_ARTISTI, "artisti.json")


class ArtistArtwork:
    def __init__(self, tag_cache=None, radici=None):
        self.tag_cache = tag_cache if isinstance(tag_cache, dict) else {}
        self.radici = list(radici or [])
        self.tag_file = {}
        self.lock = threading.RLock()
        try:
            with open(CACHE_ARTISTI_INDEX, encoding="utf-8") as stream:
                self.file_index = json.load(stream)
        except Exception:
            self.file_index = {}
        if not isinstance(self.file_index, dict):
            self.file_index = {}
        self.dirty = 0
        self.artisti_mem = {}

    def artista_del_file(self, percorso):
        if not percorso or not os.path.isabs(percorso) or os.path.splitext(percorso)[1][1:].lower() not in AUDIO:
            return ""
        try:
            stato = os.stat(percorso)
            firma = [int(getattr(stato, "st_mtime_ns", stato.st_mtime * 1e9)),
                     int(stato.st_size)]
        except OSError:
            return ""
        with self.lock:
            voce = self.file_index.get(percorso)
            if isinstance(voce, list) and len(voce) == 3 and voce[:2] == firma:
                return str(voce[2] or "")
            tag = self.tag_file.get(percorso)
        if not tag:
            tag = tag_di(percorso, self.tag_cache)
        artista = (tag[1] if tag and len(tag) > 1 else "").strip()
        if not artista:
            _titolo, artista, _album, _anno = dal_percorso(percorso, self.radici)
        artista = str(artista or "").strip()
        with self.lock:
            self.tag_file[percorso] = tag
            self.file_index[percorso] = firma + [artista]
            self.artisti_mem[artista.casefold()] = artista
            self.dirty += 1
            salva = self.dirty >= 8
        if salva:
            self.salva_cache()
        return artista

    def salva_cache(self):
        with self.lock:
            if not self.dirty:
                return
            try:
                os.makedirs(CACHE_ARTISTI, exist_ok=True)
                temporaneo = CACHE_ARTISTI_INDEX + ".tmp"
                with open(temporaneo, "w", encoding="utf-8") as stream:
                    json.dump(self.file_index, stream, ensure_ascii=False,
                              separators=(",", ":"))
                os.replace(temporaneo, CACHE_ARTISTI_INDEX)
                self.dirty = 0
            except Exception:
                pass

    @staticmethod
    def percorso_foto(artista):
        chiave = hashlib.sha256(artista.casefold().encode("utf-8")).hexdigest()
        return os.path.join(CACHE_ARTISTI, chiave + ".jpg")

    def scarica_foto(self, artista):
        if not artista:
            return None
        os.makedirs(CACHE_ARTISTI, exist_ok=True)
        destinazione = self.percorso_foto(artista)
        if os.path.isfile(destinazione) and os.path.getsize(destinazione) > 0:
            return destinazione
        mancata = destinazione + ".miss"
        try:
            if os.path.isfile(mancata) and time.time() - os.path.getmtime(mancata) < 7 * 86400:
                return None
        except OSError:
            pass
        try:
            url = "https://www.theaudiodb.com/api/v1/json/123/search.php?s=" + quote(artista)
            richiesta = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(richiesta, timeout=12) as risposta:
                dati = json.loads(risposta.read(2 * 1024 * 1024).decode("utf-8", "replace"))
            artisti = dati.get("artists") or []
            cercato = " ".join(artista.casefold().split())
            trovato = next((voce for voce in artisti
                            if " ".join(str(voce.get("strArtist") or "").casefold().split()) == cercato),
                           None)
            if trovato is None and len(artisti) == 1:
                trovato = artisti[0]
            if trovato is None:
                open(mancata, "w").close()
                return None
            immagine = next((trovato.get(k) for k in (
                "strArtistFanart", "strArtistFanart2", "strArtistFanart3",
                "strArtistFanart4", "strArtistThumb", "strArtistBanner"
            ) if trovato.get(k)), None)
            if not immagine:
                open(mancata, "w").close()
                return None
            richiesta = Request(immagine, headers={"User-Agent": UA})
            with urlopen(richiesta, timeout=18) as risposta:
                contenuto = risposta.read(15 * 1024 * 1024)
            if not contenuto:
                return None
            try:
                from PIL import Image
                import io
                with Image.open(io.BytesIO(contenuto)) as originale:
                    immagine = originale.convert("RGB")
                    immagine.thumbnail((1600, 1000), Image.LANCZOS)
                    immagine.save(destinazione, "JPEG", quality=88, optimize=True)
            except ImportError:
                with open(destinazione, "wb") as stream:
                    stream.write(contenuto)
            try:
                os.remove(mancata)
            except OSError:
                pass
            return destinazione if os.path.isfile(destinazione) else None
        except Exception:
            return None
