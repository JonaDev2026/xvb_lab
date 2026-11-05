import bisect
import hashlib
import calendar
import gzip
import os
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import CASA, REGISTRAZIONI
from .playlists import UA

EPG_VECCHIA = 6 * 3600
CACHE_EPG = os.path.join(CASA, ".cache", "xvb", "epg")
POSTER_H = 192
CACHE_POSTER = os.path.join(CASA, ".cache", "xvb", "poster")
EPG_ICONE = {}
EPG_ICONE_NOME = {}

def guide_da_aggiornare(percorsi, caricata_il, tentata_il, ora=None):
    ora = time.time() if ora is None else ora
    if not percorsi or ora - tentata_il < 3600:
        return False
    for dove in percorsi:
        if os.path.isfile(dove):
            try:
                if os.path.getmtime(dove) > caricata_il:
                    return True
            except OSError:
                continue
        else:
            cache = os.path.join(CACHE_EPG, hashlib.md5(dove.encode()).hexdigest())
            try:
                if not os.path.isfile(cache) or ora - os.path.getmtime(cache) >= EPG_VECCHIA:
                    return True
            except OSError:
                return True
    return False


def ora_xmltv(t):
    m = re.match(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})?\s*([+-]\d{4})?", t or "")
    if not m:
        return None
    y, mo, d, h, mi = (int(x) for x in m.groups()[:5])
    se = int(m.group(6) or 0)
    utc = calendar.timegm((y, mo, d, h, mi, se, 0, 0, 0))
    z = m.group(7)
    if z:
        scarto = (int(z[1:3]) * 60 + int(z[3:5])) * 60
        utc -= scarto if z[0] == "+" else -scarto
    return utc


def prendi_epg(dove):
    if os.path.isfile(dove):
        return dove
    os.makedirs(CACHE_EPG, exist_ok=True)
    f = os.path.join(CACHE_EPG, hashlib.md5(dove.encode()).hexdigest())
    if os.path.isfile(f) and time.time() - os.path.getmtime(f) < EPG_VECCHIA:
        return f
    try:
        richiesta = Request(dove, headers={"User-Agent": UA})
        dati = urlopen(richiesta, timeout=60).read()
    except Exception:
        if os.path.isfile(f):
            return f
        raise
    with open(f + ".part", "wb") as stream:
        stream.write(dati)
    os.replace(f + ".part", f)
    return f


def unisci_programmi(base, altri):
    if not altri:
        return base
    if not base:
        return list(altri)
    res = list(base)
    inizi = [b_[0] for b_ in res]
    for s_, e_, t_ in altri:
        i = bisect.bisect_left(inizi, e_)
        if i > 0 and res[i - 1][1] > s_:
            continue
        res.insert(i, (s_, e_, t_))
        inizi.insert(i, s_)
    return res


def unisci_guide(guide):
    padre = {}

    def radice(x):
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    per_nome = {}
    for nomi, _programmi in guide:
        for nome, ide in nomi.items():
            if ide:
                per_nome.setdefault(nome, []).append(ide)
    for ids in per_nome.values():
        for ide in ids[1:]:
            padre[radice(ide)] = radice(ids[0])
    for _nomi, programmi in guide:
        for ide in programmi:
            if ide:
                radice(ide)
    gruppi = {}
    for ide in list(padre):
        gruppi.setdefault(radice(ide), []).append(ide)
    programmi_uniti = {}
    for _nomi, programmi in guide:
        if "" in programmi:
            programmi_uniti.setdefault("", programmi[""])
    for ids in gruppi.values():
        lista = []
        for _nomi, programmi in guide:
            for ide in ids:
                if ide in programmi:
                    lista = unisci_programmi(lista, programmi[ide])
        if lista:
            for ide in ids:
                programmi_uniti[ide] = lista
    nomi_tutti = {}
    for nomi, _programmi in guide:
        for nome, ide in nomi.items():
            nomi_tutti.setdefault(nome, ide)
    return nomi_tutti, programmi_uniti


def piu_nuova(a, b):
    def pezzi(v):
        return [int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", v)]
    return pezzi(a) > pezzi(b)


def registrazioni():
    gruppi = {}
    try:
        voci = os.listdir(REGISTRAZIONI)
    except Exception:
        return []
    for n in voci:
        p = os.path.join(REGISTRAZIONI, n)
        if os.path.isdir(p):
            canale, file_ = n, [os.path.join(p, f) for f in os.listdir(p)]
        else:
            canale, file_ = "xvb", [p]
        for f in file_:
            if not f.lower().endswith((".mkv", ".mka", ".mp4", ".ts")):
                continue
            base = os.path.splitext(os.path.basename(f))[0]
            m = re.search(r"(\d{4})-(\d{2})-(\d{2}) (\d{2})-(\d{2})$", base)
            if m:
                giorno = "%s-%s-%s" % m.group(1, 2, 3)
                ora = "%s:%s" % m.group(4, 5)
                titolo = base[:m.start()].rstrip(" -") or base
            else:
                t = time.localtime(os.path.getmtime(f))
                giorno, ora, titolo = time.strftime("%Y-%m-%d", t), time.strftime("%H:%M", t), base
            gruppi.setdefault((canale, giorno), []).append((ora, titolo, f))
    fuori = sorted(gruppi.items(), key=lambda kv: (kv[0][1], kv[0][0]), reverse=True)
    return [(k, sorted(v)) for k, v in fuori]


def nome_dentro(f):
    try:
        with open(f, "rb") as stream:
            testa = stream.read(4096)
        if testa[:2] != b"\x1f\x8b":
            return None
        flag, p = testa[3], 10
        if flag & 4:
            p += 2 + int.from_bytes(testa[p:p + 2], "little")
        if flag & 8:
            fine = testa.index(b"\x00", p)
            nome = os.path.basename(testa[p:fine].decode("latin-1").strip())
            return nome or None
    except Exception:
        pass
    return None


def nome_epg(dove):
    if re.match(r"https?://", dove, re.I):
        u = urlparse(dove)
        dominio = u.netloc.lower()
        if dominio.startswith("www."):
            dominio = dominio[4:]
        nome = os.path.basename(u.path.rstrip("/"))
        if not nome:
            return dominio
    else:
        nome = os.path.basename(dove.rstrip("/")) or dove
    nome = re.sub(r"\.gz$", "", nome, flags=re.I)
    return nome if nome.lower().endswith(".xml") else nome + ".xml"


def nome_piatto(nome):
    n = re.sub(r"[^a-z0-9]+", "", (nome or "").lower())
    return re.sub(r"(fhd|uhd|hd|4k|sd)$", "", n)


def icona_programma_epg(ide, nome, programma):
    if not programma:
        return None
    inizio, _fine, titolo = programma
    src = EPG_ICONE.get((ide or "", inizio))
    if src:
        return src
    return EPG_ICONE_NOME.get((nome_piatto(nome), inizio, nome_piatto(titolo)))


def leggi_epg(f):
    with open(f, "rb") as stream:
        testa = stream.read(2)
    apri = gzip.open if testa == b"\x1f\x8b" else open
    nomi, programmi, nomi_per_id = {}, {}, {}
    da = time.time() - 3600
    with apri(f, "rb") as stream:
        for _ev, el in ET.iterparse(stream):
            if el.tag == "channel":
                ide = el.get("id") or ""
                for n in el.findall("display-name"):
                    if n.text and n.text.strip():
                        chiave = nome_piatto(n.text)
                        nomi.setdefault(chiave, ide)
                        nomi_per_id.setdefault(ide, set()).add(chiave)
                el.clear()
            elif el.tag == "programme":
                inizio, fine = ora_xmltv(el.get("start")), ora_xmltv(el.get("stop"))
                if inizio is not None and fine is not None and fine >= da:
                    t = el.find("title")
                    titolo = (t.text or "").strip() if t is not None else ""
                    programmi.setdefault(el.get("channel") or "", []).append((inizio, fine, titolo))
                    ic = el.find("icon")
                    if ic is not None and ic.get("src"):
                        src = ic.get("src")
                        ide = el.get("channel") or ""
                        EPG_ICONE.setdefault((ide, inizio), src)
                        titolo_key = nome_piatto(titolo)
                        for nome_key in nomi_per_id.get(ide, ()):
                            EPG_ICONE_NOME.setdefault((nome_key, inizio, titolo_key), src)
                el.clear()
    for lista in programmi.values():
        lista.sort()
    return nomi, programmi
