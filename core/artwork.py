import os

from .config import QUI
from .constants import PUNTO
from .colors import HA_PIL

if HA_PIL:
    from PIL import Image, ImageDraw

_MASCHERE_DISCO = {}
_ANELLI_DISCO = {}


def disco_base(percorso, lato):
    immagine = Image.open(percorso).convert("RGBA")
    lato_base = min(immagine.size)
    x0, y0 = (immagine.width - lato_base) // 2, (immagine.height - lato_base) // 2
    return immagine.crop((x0, y0, x0 + lato_base, y0 + lato_base)).resize(
        (lato, lato), Image.Resampling.LANCZOS
    )


def disco_frame(base, larga, alta, angolo=0.0, colore=None):
    lato = base.width
    if lato not in _MASCHERE_DISCO:
        maschera = Image.new("L", (lato, lato), 0)
        disegno = ImageDraw.Draw(maschera)
        disegno.ellipse([0, 0, lato - 1, lato - 1], fill=255)
        raggio = lato * 0.075
        disegno.ellipse([lato / 2.0 - raggio, lato / 2.0 - raggio,
                         lato / 2.0 + raggio, lato / 2.0 + raggio], fill=0)
        _MASCHERE_DISCO[lato] = maschera
    immagine = base.rotate(-angolo, resample=Image.Resampling.BICUBIC) if angolo else base.copy()
    immagine.putalpha(_MASCHERE_DISCO[lato])
    if colore and (lato, colore) not in _ANELLI_DISCO:
        try:
            overlay = Image.new("RGBA", (lato, lato), (0, 0, 0, 0))
            disegno = ImageDraw.Draw(overlay)
            raggio, foro = lato * 0.19, lato * 0.075
            disegno.ellipse([lato / 2.0 - raggio, lato / 2.0 - raggio,
                             lato / 2.0 + raggio, lato / 2.0 + raggio], fill=colore)
            disegno.ellipse([lato / 2.0 - foro, lato / 2.0 - foro,
                             lato / 2.0 + foro, lato / 2.0 + foro], fill=(0, 0, 0, 0))
        except Exception:
            overlay = None
        _ANELLI_DISCO[(lato, colore)] = overlay
    if colore and _ANELLI_DISCO.get((lato, colore)) is not None:
        immagine.alpha_composite(_ANELLI_DISCO[(lato, colore)])
    immagine = immagine.resize((alta, alta), Image.Resampling.LANCZOS)
    riquadro = Image.new("RGBA", (larga, alta), (0, 0, 0, 0))
    riquadro.alpha_composite(immagine, ((larga - alta) // 2, 0))
    return riquadro


def pallino(colore, lato=PUNTO):
    raggio = lato * 0.22
    centro = lato / 2.0
    if HA_PIL:
        scala = 4
        immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
        ImageDraw.Draw(immagine).ellipse(
            [(centro - raggio) * scala, (centro - raggio) * scala,
             (centro + raggio) * scala, (centro + raggio) * scala], fill=colore
        )
        return immagine.resize((lato, lato), Image.Resampling.LANCZOS)
    return None


def qualita(alta, banda):
    if alta >= 2160:
        return "2160p", "#bf5af2"
    if alta >= 1080:
        return "1080p", "#30d158"
    if alta >= 720:
        return "720p", "#0a84ff"
    if alta >= 480:
        return "%dp" % alta, "#ff9f0a"
    if alta > 0:
        return "%dp" % alta, "#ff5257"
    from .colors import GRIGIO
    return "%.0f kbit/s" % (banda / 1000.0), GRIGIO


def nel_riquadro(immagine, lato, dentro):
    dimensione = dentro or lato
    immagine = immagine.resize((dimensione, dimensione), Image.Resampling.LANCZOS)
    if dimensione == lato:
        return immagine
    riquadro = Image.new("RGBA", (lato, lato), (0, 0, 0, 0))
    riquadro.paste(immagine, ((lato - dimensione) // 2, (lato - dimensione) // 2))
    return riquadro


def cartellina(colore, aperta=False, lato=PUNTO, dentro=None):
    if not HA_PIL:
        return None
    scala = 4
    immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
    disegno = ImageDraw.Draw(immagine)
    unita = lato * scala / 24.0
    spessore = int(1.7 * unita)
    disegno.line([(3 * unita, 19 * unita), (3 * unita, 5 * unita),
                  (10 * unita, 5 * unita), (12 * unita, 7.5 * unita),
                  (21 * unita, 7.5 * unita), (21 * unita, 19 * unita),
                  (3 * unita, 19 * unita)], fill=colore, width=spessore, joint="curve")
    if aperta:
        disegno.line([(3 * unita, 19 * unita), (6 * unita, 11.5 * unita),
                      (23 * unita, 11.5 * unita), (20 * unita, 19 * unita)],
                     fill=colore, width=spessore, joint="curve")
    return nel_riquadro(immagine, lato, dentro)


def segnalibro(colore, lato=PUNTO, dentro=None):
    if not HA_PIL:
        return None
    scala = 4
    immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
    fattore = lato * scala * 0.76 / 514.0

    def punto(x, y):
        return ((x - 320) * fattore + lato * scala / 2.0,
                (y - 318) * fattore + lato * scala / 2.0)

    def curva(a, b, c, d):
        punti = []
        for i in range(1, 11):
            t = i / 10.0
            m = 1 - t
            punti.append(punto(
                m ** 3 * a[0] + 3 * m * m * t * b[0] + 3 * m * t * t * c[0] + t ** 3 * d[0],
                m ** 3 * a[1] + 3 * m * m * t * b[1] + 3 * m * t * t * c[1] + t ** 3 * d[1]
            ))
        return punti

    punti = [punto(192, 64)]
    punti += curva((192, 64), (156.7, 64), (128, 92.7), (128, 128))
    punti += [punto(128, 544)]
    punti += curva((128, 544), (128, 555.5), (134.2, 566.2), (144.2, 571.8))
    punti += curva((144.2, 571.8), (154.2, 577.4), (166.5, 577.3), (176.4, 571.4))
    punti += [punto(320, 485.3), punto(463.5, 571.4)]
    punti += curva((463.5, 571.4), (473.4, 577.3), (485.7, 577.5), (495.7, 571.8))
    punti += curva((495.7, 571.8), (505.7, 566.1), (512, 555.5), (512, 544))
    punti += [punto(512, 128)]
    punti += curva((512, 128), (512, 92.7), (483.3, 64), (448, 64))
    ImageDraw.Draw(immagine).line(
        punti + punti[:2], fill=colore, width=int(1.7 * lato * scala / 24.0), joint="curve"
    )
    return nel_riquadro(immagine, lato, dentro)


def globo(colore, lato=PUNTO, dentro=None):
    if not HA_PIL:
        return None
    scala = 4
    immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
    disegno = ImageDraw.Draw(immagine)
    unita = lato * scala / 24.0
    spessore = int(1.7 * unita)
    disegno.ellipse((3 * unita, 3 * unita, 21 * unita, 21 * unita), outline=colore, width=spessore)
    disegno.ellipse((8 * unita, 3 * unita, 16 * unita, 21 * unita), outline=colore, width=spessore)
    disegno.line([(3 * unita, 12 * unita), (21 * unita, 12 * unita)], fill=colore, width=spessore)
    disegno.line([(5 * unita, 7.5 * unita), (19 * unita, 7.5 * unita)], fill=colore, width=spessore)
    disegno.line([(5 * unita, 16.5 * unita), (19 * unita, 16.5 * unita)], fill=colore, width=spessore)
    return nel_riquadro(immagine, lato, dentro)


def disco(colore, lato=PUNTO, alta=None, dentro=None):
    if not HA_PIL:
        return None
    percorso = os.path.join(QUI, "icone", "disco.png")
    if os.path.isfile(percorso):
        try:
            immagine = Image.open(percorso).convert("RGBA")
            larghezza, altezza = lato, alta or lato
            scala = min((dentro or larghezza) / float(max(1, immagine.width)), (dentro or altezza) / float(max(1, immagine.height)))
            immagine = immagine.resize((max(1, int(immagine.width * scala)), max(1, int(immagine.height * scala))), Image.Resampling.LANCZOS)
            riquadro = Image.new("RGBA", (larghezza, altezza), (0, 0, 0, 0))
            riquadro.alpha_composite(immagine, ((larghezza - immagine.width) // 2, (altezza - immagine.height) // 2))
            return riquadro
        except Exception:
            pass
    scala = 4
    immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
    disegno = ImageDraw.Draw(immagine)
    unita = lato * scala / 24.0
    spessore = int(1.7 * unita)
    disegno.ellipse((3 * unita, 3 * unita, 21 * unita, 21 * unita), outline=colore, width=spessore)
    disegno.ellipse((9.5 * unita, 9.5 * unita, 14.5 * unita, 14.5 * unita), outline=colore, width=spessore)
    disegno.arc((6 * unita, 6 * unita, 18 * unita, 18 * unita), 200, 250,
                fill=colore, width=int(1.2 * unita))
    return nel_riquadro(immagine, lato, dentro)


def vinile(colore, lato=PUNTO, dentro=None):
    if not HA_PIL:
        return None
    scala = 4
    immagine = Image.new("RGBA", (lato * scala, lato * scala), (0, 0, 0, 0))
    disegno = ImageDraw.Draw(immagine)
    unita = lato * scala / 24.0
    centro = 12 * unita

    def cerchio(raggio, **opzioni):
        disegno.ellipse((centro - raggio * unita, centro - raggio * unita,
                         centro + raggio * unita, centro + raggio * unita), **opzioni)

    cerchio(11.4, fill=(24, 24, 28, 255), outline="#6a6a74", width=max(1, int(1.2 * unita)))
    cerchio(9.2, outline=(72, 72, 80, 255), width=max(1, int(0.5 * unita)))
    cerchio(7.2, outline=(72, 72, 80, 255), width=max(1, int(0.5 * unita)))
    cerchio(5.2, fill=colore)
    cerchio(1.9, fill=(0, 0, 0, 0))
    return nel_riquadro(immagine, lato, dentro)


def premoltiplica(immagine):
    from PIL import ImageChops
    r, g, b, a = immagine.convert("RGBA").split()
    return Image.merge("RGBA", (ImageChops.multiply(r, a), ImageChops.multiply(g, a),
                                 ImageChops.multiply(b, a), a))
