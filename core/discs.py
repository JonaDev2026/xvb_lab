import os
import re


def dischi():
    risultati = []
    try:
        with open("/proc/mounts", encoding="utf-8", errors="ignore") as stream:
            for riga in stream:
                parti = riga.split()
                if len(parti) >= 3 and parti[2] in ("iso9660", "udf"):
                    punto = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), parti[1])
                    if os.path.isdir(punto):
                        risultati.append((punto, os.path.basename(punto.rstrip(os.sep)) or punto))
    except Exception:
        pass
    return risultati


def dvd_cifrato(mountpoint):
    try:
        cartella = next(os.path.join(mountpoint, nome) for nome in ("VIDEO_TS", "video_ts")
                        if os.path.isdir(os.path.join(mountpoint, nome)))
        vob = [os.path.join(cartella, nome) for nome in os.listdir(cartella)
               if nome.upper().endswith(".VOB") and not nome.upper().startswith("VIDEO_TS")]
        if not vob:
            return True
        percorso = max(vob, key=os.path.getsize)
        settori = os.path.getsize(percorso) // 2048
        visti = 0
        with open(percorso, "rb") as stream:
            for indice in range(200):
                stream.seek((settori * indice // 200) * 2048)
                settore = stream.read(2048)
                if (len(settore) < 2048 or settore[:4] != b"\x00\x00\x01\xba"
                        or (settore[4] & 0xC0) != 0x40):
                    continue
                posizione = 14 + (settore[13] & 7)
                if (settore[posizione:posizione + 3] != b"\x00\x00\x01"
                        or not (settore[posizione + 3] == 0xBD
                                or 0xC0 <= settore[posizione + 3] <= 0xEF)):
                    continue
                visti += 1
                if (settore[posizione + 6] >> 4) & 3:
                    return True
        return visti == 0
    except Exception:
        return True


def cd_audio():
    risultati = []
    try:
        lettori = sorted(nome for nome in os.listdir("/sys/block") if nome.startswith("sr"))
    except OSError:
        return risultati
    for nome in lettori:
        try:
            with open("/sys/block/%s/dev" % nome) as stream:
                dispositivo = stream.read().strip()
            with open("/run/udev/data/b" + dispositivo, encoding="utf-8", errors="ignore") as stream:
                dati = stream.read()
        except OSError:
            continue
        match = re.search(r"^E:ID_CDROM_MEDIA_TRACK_COUNT_AUDIO=(\d+)", dati, re.M)
        if match and int(match.group(1)) > 0:
            risultati.append(("/dev/" + nome, int(match.group(1))))
    return risultati


def e_cd(url):
    return url.startswith("cdda://")


def titolo_da_etichetta(etichetta):
    titolo = re.sub(r"[_.]+", " ", etichetta)
    titolo = re.sub(
        r"\b(DISC|DISK|CD|D)\s*\d\b|\b(DVD|DVD9|DVD5|PAL|NTSC|WS|FS|R\d|UK|US|EU|SE)\b",
        " ", titolo, flags=re.I
    )
    return re.sub(r"\s+", " ", titolo).strip().title() or etichetta


def e_dvd(mountpoint):
    return any(os.path.isdir(os.path.join(mountpoint, nome))
               for nome in ("VIDEO_TS", "video_ts"))
