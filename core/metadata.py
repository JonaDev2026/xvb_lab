import hashlib
import json
import os
import re
from urllib.request import Request, urlopen

from .config import CASA, CONFIG_DIR, CACHE_DIR
from .constants import VERSIONE
from .media import AUDIO

COPERTINE_URL = os.path.join(CONFIG_DIR, "copertine")
TMDB = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"
FILE_PROVATI = os.path.join(CACHE_DIR, "info_provate.json")
FILE_INFO = os.path.join(CACHE_DIR, "info.json")
LINGUE_TMDB = {"en": "en-US", "it": "it-IT", "es": "es-ES", "fr": "fr-FR",
               "de": "de-DE", "pt": "pt-BR", "ru": "ru-RU"}
UA_XVB = "XVB5/%s ( https://github.com/JonaDev2026/xvb_lab )"


def copertina_url(url):
    return os.path.join(COPERTINE_URL, hashlib.md5(url.encode("utf-8")).hexdigest() + ".jpg")


def copertina_dentro(percorso):
    try:
        import mutagen
        tag = mutagen.File(percorso)
        if tag is None:
            return None
        if getattr(tag, "pictures", None):
            return tag.pictures[0].data
        if tag.tags:
            for chiave in tag.tags.keys():
                if str(chiave).startswith("APIC"):
                    return tag.tags[chiave].data
            if "covr" in tag.tags:
                return bytes(tag.tags["covr"][0])
            if "metadata_block_picture" in tag.tags:
                import base64
                from mutagen.flac import Picture
                return Picture(base64.b64decode(tag.tags["metadata_block_picture"][0])).data
    except Exception:
        pass
    return None


def leggi_json(percorso):
    try:
        with open(percorso, encoding="utf-8") as stream:
            return json.load(stream)
    except Exception:
        return {}


def scrivi_json(percorso, dati):
    try:
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with open(percorso, "w", encoding="utf-8") as stream:
            json.dump(dati, stream)
    except Exception:
        pass


def titolo_anno(percorso):
    for testo in (os.path.splitext(os.path.basename(percorso))[0],
                  os.path.basename(os.path.dirname(percorso))):
        match = re.match(r"^(.*?)[\s._\-\(\[]+((?:19|20)\d{2})(?:\D|$)", testo)
        if match and match.group(1).strip():
            return re.sub(r"[._]+", " ", match.group(1)).strip(), match.group(2)
    titolo = re.sub(r"[._]+", " ", os.path.splitext(os.path.basename(percorso))[0]).strip()
    return titolo, None


def json_da(url, intestazioni=None):
    richiesta = Request(url, headers=dict(
        {"User-Agent": UA_XVB % VERSIONE, "Accept": "application/json"},
        **(intestazioni or {})
    ))
    return json.loads(urlopen(richiesta, timeout=15).read().decode("utf-8"))


def scarica_in(url, destinazione):
    richiesta = Request(url, headers={"User-Agent": UA_XVB % VERSIONE})
    dati = urlopen(richiesta, timeout=20).read()
    if len(dati) < 500:
        raise ValueError("empty image")
    with open(destinazione, "wb") as stream:
        stream.write(dati)


def _anno_via(titolo):
    anno = ""
    match = re.search(r"[\(\[]\s*((?:19|20)\d\d)\s*[\)\]]", titolo)
    if match:
        anno = match.group(1)
        titolo = titolo[:match.start()] + titolo[match.end():]
    else:
        match = re.match(r"\s*((?:19|20)\d\d)\s*[-.\u2013]\s*(.+)$", titolo) or \
            re.match(r"(.+?)\s*[-\u2013]\s*((?:19|20)\d\d)\s*$", titolo)
        if match:
            a, b = match.groups()
            anno, titolo = (a, b) if a.isdigit() else (b, a)
    return re.sub(r"\s+", " ", titolo.replace("_", " ")).strip(" -\u2013."), anno


def dal_percorso(percorso, radici=()):
    cartella, nome = os.path.split(percorso)
    radice = os.path.splitext(nome)[0].replace("_", " ")
    radici = [os.path.normpath(r) for r in radici]
    titolo = re.sub(r"^\s*\d{1,3}\s*[-.\s]\s*", "", radice).strip()
    artista = album = anno = ""
    if " - " in titolo:
        artista, titolo = (parte.strip() for parte in titolo.split(" - ", 1))
    padre = os.path.basename(cartella)
    nonno_path = os.path.dirname(cartella)
    nonno = os.path.basename(nonno_path)
    if os.path.normpath(cartella) not in radici and padre:
        if " - " in padre and not re.match(r"\s*(19|20)\d\d\s*-", padre):
            a, b = padre.split(" - ", 1)
            artista = artista or a.strip()
            album, anno = _anno_via(b)
        else:
            album, anno = _anno_via(padre)
            if nonno and os.path.normpath(nonno_path) not in radici:
                if not artista:
                    artista = nonno.replace("_", " ").strip()
            elif not anno and not artista:
                artista, album = album, ""
    if artista and album.lower() == artista.lower():
        album = ""
    return titolo or radice, artista, album, anno


def poster_film(percorso):
    cartella, base = os.path.split(percorso)
    radice = os.path.splitext(base)[0]
    nomi = ([radice + estensione for estensione in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")] +
            [nome + estensione for nome in ("poster", "folder", "cover")
             for estensione in (".jpg", ".jpeg", ".png")])
    return next((os.path.join(cartella, nome) for nome in nomi
                 if os.path.isfile(os.path.join(cartella, nome))), None)

def copertina_musicbrainz(artista, album):
    from urllib.parse import quote
    query = 'releasegroup:"%s" AND artist:"%s"' % (album.replace('"', ""), artista.replace('"', ""))
    risultati = json_da("https://musicbrainz.org/ws/2/release-group/?fmt=json&limit=3&query=" + quote(query))
    for gruppo in risultati.get("release-groups") or []:
        if gruppo.get("id"):
            return ("https://coverartarchive.org/release-group/%s/front-500" % gruppo["id"],
                    (gruppo.get("first-release-date") or "")[:4])
    return None, ""


def copertina_da_brano(artista, titolo):
    from urllib.parse import quote
    query = 'recording:"%s" AND artist:"%s"' % (titolo.replace('"', ""), artista.replace('"', ""))
    risultati = json_da("https://musicbrainz.org/ws/2/recording/?fmt=json&limit=15&query=" + quote(query))
    scelte = []
    for registrazione in risultati.get("recordings") or []:
        for pubblicazione in registrazione.get("releases") or []:
            gruppo = pubblicazione.get("release-group") or {}
            if not gruppo.get("id"):
                continue
            buono = (pubblicazione.get("status", "Official") == "Official"
                     and gruppo.get("primary-type") in ("Album", "EP", "Single")
                     and not gruppo.get("secondary-types"))
            data = pubblicazione.get("date") or "9999"
            scelte.append((not buono, gruppo.get("primary-type") != "Album", data,
                           gruppo["id"], gruppo.get("title") or pubblicazione.get("title") or ""))
    if not scelte:
        return [], "", ""
    scelte.sort()
    _non_buono, _non_album, data, _id_gruppo, nome = scelte[0]
    urls = []
    for scelta in scelte:
        url = "https://coverartarchive.org/release-group/%s/front-500" % scelta[3]
        if url not in urls:
            urls.append(url)
    return urls[:3], (data[:4] if data[:4].isdigit() and data != "9999" else ""), nome

TMDB_CHIAVE = ("eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxMzIxMjRhMzU0YjRmYzE4NGVmYjgwODk5NzZmMWVmMiIsIm5iZiI6"
               "MTc5MDc3MTY0OS4zODYsInN1YiI6IjZhYmQwMWMxOTkyNzRmMGQxOTFlN2JjYiIsInNjb3BlcyI6WyJhcGlf"
               "cmVhZCJdLCJ2ZXJzaW9uIjoxfQ.AYShiHv1HdbN0Wj1l0co9D6CIFcOy5NAM5WkMZyQQ0M")


def _tmdb(chiave, strada, parametri):
    from urllib.parse import urlencode
    if len(chiave) > 40:
        intestazioni = {"Authorization": "Bearer " + chiave}
    else:
        intestazioni, parametri = None, dict(parametri, api_key=chiave)
    return json_da("%s/%s?%s" % (TMDB, strada, urlencode(parametri)), intestazioni)


def generi_tmdb(chiave, lingua, cache):
    chiave_cache = "_generi_" + lingua
    if chiave_cache not in cache:
        nomi = {}
        for tipo in ("movie", "tv"):
            for genere in _tmdb(chiave, "genre/%s/list" % tipo,
                                {"language": lingua}).get("genres") or []:
                nomi[str(genere["id"])] = genere["name"]
        cache[chiave_cache] = nomi
    return cache[chiave_cache]


def info_tmdb(chiave, titolo, anno, lingua):
    for tipo, campo_anno, campo_nome, campo_data in (
        ("movie", "year", "title", "release_date"),
        ("tv", "first_air_date_year", "name", "first_air_date")
    ):
        parametri = {"query": titolo, "include_adult": "false", "language": lingua}
        if anno:
            parametri[campo_anno] = anno
        risultati = _tmdb(chiave, "search/" + tipo, parametri).get("results") or []
        if risultati:
            risultato = next((voce for voce in risultati if voce.get("poster_path")), risultati[0])
            return {
                "titolo": risultato.get(campo_nome) or "",
                "anno": (risultato.get(campo_data) or "")[:4],
                "generi": [str(genere) for genere in risultato.get("genre_ids") or []],
                "voto": risultato.get("vote_average") or 0,
                "voti": risultato.get("vote_count") or 0,
                "poster": TMDB_IMG + risultato["poster_path"] if risultato.get("poster_path") else ""
            }
    return None
