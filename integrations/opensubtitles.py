import io
import json
import os
import re
import time
import zipfile
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PySide6.QtCore import QThread, Signal

from core.constants import VERSIONE


class RicercaSottotitoli(QThread):
    completato = Signal(str, str, object, str)
    errore = Signal(str)

    def __init__(self, api_key, username, password, titolo, lingue):
        super().__init__()
        self.api_key = api_key
        self.username = username
        self.password = password
        self.titolo = titolo
        self.lingue = lingue

    def run(self):
        try:
            intestazioni = {
                "Api-Key": self.api_key,
                "User-Agent": "XVB Player v" + VERSIONE,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            corpo = json.dumps({
                "username": self.username,
                "password": self.password,
            }).encode("utf-8")
            richiesta = Request(
                "https://api.opensubtitles.com/api/v1/login",
                data=corpo, headers=intestazioni, method="POST")
            try:
                with urlopen(richiesta, timeout=30) as risposta:
                    login = json.loads(risposta.read().decode("utf-8", "replace"))
            except HTTPError as errore:
                dettaglio = errore.read().decode("utf-8", "replace")
                try:
                    dettaglio = json.loads(dettaglio).get("message", dettaglio)
                except Exception:
                    pass
                raise RuntimeError("OpenSubtitles login HTTP %s: %s" % (errore.code, dettaglio))
            token = login.get("token")
            if not token:
                raise RuntimeError(login.get("message") or "OpenSubtitles login failed")
            host = str(login.get("base_url") or "api.opensubtitles.com").strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = "https://" + host
            base_url = host if host.endswith("/api/v1") else host + "/api/v1"
            parametri = urlencode({
                "query": self.titolo,
                "languages": self.lingue,
                "order_by": "download_count",
                "order_direction": "desc",
            })
            ricerca = Request(
                base_url + "/subtitles?" + parametri,
                headers={
                    "Api-Key": self.api_key,
                    "Authorization": "Bearer " + token,
                    "User-Agent": "XVB Player v" + VERSIONE,
                    "Accept": "application/json",
                })
            with urlopen(ricerca, timeout=30) as risposta:
                dati = json.loads(risposta.read().decode("utf-8", "replace"))
            self.completato.emit(self.api_key, token, dati.get("data", []), base_url)
        except Exception as errore:
            self.errore.emit(str(errore))


class ScaricaSottotitolo(QThread):
    completato = Signal(str)
    errore = Signal(str)

    def __init__(self, api_key, token, base_url, file_id, lingua, titolo):
        super().__init__()
        self.api_key = api_key
        self.token = token
        self.base_url = base_url
        self.file_id = file_id
        self.lingua = lingua
        self.titolo = titolo

    def run(self):
        try:
            corpo = json.dumps({"file_id": self.file_id}).encode("utf-8")
            richiesta = Request(
                self.base_url.rstrip("/") + "/download",
                data=corpo,
                headers={
                    "Api-Key": self.api_key,
                    "Authorization": "Bearer " + self.token,
                    "User-Agent": "XVB Player v" + VERSIONE,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                method="POST")
            try:
                with urlopen(richiesta, timeout=30) as risposta:
                    dati = json.loads(risposta.read().decode("utf-8", "replace"))
            except HTTPError as errore:
                dettaglio = errore.read().decode("utf-8", "replace")
                try:
                    dettaglio = json.loads(dettaglio).get("message", dettaglio)
                except Exception:
                    pass
                raise RuntimeError("OpenSubtitles download HTTP %s: %s" % (errore.code, dettaglio))
            link = dati.get("link")
            if not link:
                raise RuntimeError(dati.get("message") or "Download URL missing")
            richiesta_file = Request(link, headers={"User-Agent": "XVB Player v" + VERSIONE})
            with urlopen(richiesta_file, timeout=45) as risposta:
                contenuto = risposta.read()
            nome_file = os.path.basename(dati.get("file_name") or "subtitle.srt")
            estensioni = (".srt", ".ass", ".ssa", ".sub", ".vtt", ".ttml")
            if zipfile.is_zipfile(io.BytesIO(contenuto)):
                with zipfile.ZipFile(io.BytesIO(contenuto)) as archivio:
                    candidati = [
                        nome for nome in archivio.namelist()
                        if not nome.endswith("/") and os.path.splitext(nome)[1].lower() in estensioni
                    ]
                    if not candidati:
                        raise RuntimeError("Archive contains no supported subtitle")
                    candidati.sort(key=lambda nome: ("forced" in nome.lower(), len(nome)))
                    selezionato = archivio.read(candidati[0])
                    nome_file = os.path.basename(candidati[0])
            else:
                selezionato = contenuto
            estensione = os.path.splitext(nome_file)[1].lower()
            if estensione not in estensioni:
                estensione = ".srt"
            cartella = os.path.join(os.path.expanduser("~"), ".cache", "xvb", "subtitles")
            os.makedirs(cartella, exist_ok=True)
            base = re.sub(r"[^\w.-]+", "_", self.titolo, flags=re.UNICODE).strip("._") or "subtitle"
            codice = re.sub(r"[^a-zA-Z0-9_-]", "", str(self.lingua)) or "sub"
            destinazione = os.path.join(cartella, "%s.%s%s" % (base, codice, estensione))
            if os.path.exists(destinazione):
                destinazione = os.path.join(
                    cartella, "%s.%s.%d%s" % (base, codice, int(time.time()), estensione))
            with open(destinazione, "wb") as stream:
                stream.write(selezionato)
            self.completato.emit(destinazione)
        except Exception as errore:
            self.errore.emit(str(errore))
