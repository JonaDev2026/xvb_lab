import os
import re
import time

from .config import REGISTRAZIONI


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


def piu_nuova(a, b):
    def pezzi(v):
        return [int(x) if x.isdigit() else 0 for x in re.split(r"[.\\-]", v)]
    return pezzi(a) > pezzi(b)
