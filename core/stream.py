import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit
from urllib.request import Request, urlopen

from .constants import UA
from .playlists import CHIAVI

_SERVER_MPD = None


def chiavi_clearkey(det):
    t = unquote((det or "").strip()).strip().strip('"').strip()
    coppie = []
    if t.startswith("{"):
        try:
            coppie = [(str(k).strip().lower(), str(v).strip().lower())
                      for k, v in json.loads(t).items()]
        except (ValueError, AttributeError):
            coppie = []
    else:
        m = re.fullmatch(r"(?:([0-9a-fA-F]{32}):)?([0-9a-fA-F]{32})", t)
        if m:
            coppie = [((m.group(1) or "").lower(), m.group(2).lower())]
    return [(k, v) for k, v in coppie
            if re.fullmatch(r"[0-9a-f]{32}", v) and int(v, 16) != 0]


def chiave_clearkey(det):
    coppie = chiavi_clearkey(det)
    return coppie[0][1] if coppie else None


def manifest_pulito(testo, url):
    testo = re.sub(
        r'\s*<AdaptationSet\b[^>]*mimeType="(?:text/|application/ttml)[^"]*"[^>]*>.*?</AdaptationSet>',
        "", testo, flags=re.S
    )
    if "<BaseURL" not in testo:
        from xml.sax.saxutils import escape
        base = escape(url.rsplit("/", 1)[0] + "/")
        testo = testo.replace("<Period", "<BaseURL>%s</BaseURL>\n<Period" % base, 1)
    return testo


def server_mpd():
    global _SERVER_MPD
    if _SERVER_MPD is not None:
        return _SERVER_MPD

    class Gestore(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                url = parse_qs(urlsplit(self.path).query)["u"][0]
                if url not in CHIAVI:
                    raise ValueError("canale senza chiave")
                testo = urlopen(Request(url, headers={"User-Agent": UA}),
                                timeout=10).read().decode("utf-8", "ignore")
                dati = manifest_pulito(testo, url).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/dash+xml")
                self.send_header("Content-Length", str(len(dati)))
                self.end_headers()
                self.wfile.write(dati)
            except Exception:
                self.send_error(502)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _SERVER_MPD = server
    return server
