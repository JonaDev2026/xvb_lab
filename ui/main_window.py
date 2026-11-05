from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon, QDesktopServices, QPixmap, QShortcut, QCursor, QTransform, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QMenu,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QSlider, QTreeWidget, QTreeWidgetItem,
    QApplication, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QStackedLayout
)
from engine.mpv import MpvVideo
from ui.widgets import Cursore, Elenco, Finestrella, Ricerca, Guida, Tendina
from ui.sidebar import Sidebar
from ui.backdrop import Sfondo
from core.artist_artwork import ArtistArtwork
from ui.handle import Maniglia
from core.session import Sessione
from core.media import media_in, AUDIO, e_media, tipo_preferiti, titolo_url, PREF_IPTV, PREF_MUSICA, PREF_VIDEO, durata_di
from core.tags import leggi_tag, tag_di, scrivi_tag
from core.metadata import (
    titolo_anno, dal_percorso, copertina_url, copertina_dentro, poster_film,
    copertina_musicbrainz, copertina_da_brano, info_tmdb, generi_tmdb,
    scarica_in, leggi_json, scrivi_json, TMDB_CHIAVE, LINGUE_TMDB,
    FILE_PROVATI, FILE_INFO,
)
from i18n import lingua_corrente
from integrations.mpris import avvia_mpris
from integrations.opensubtitles import RicercaSottotitoli, ScaricaSottotitolo
from core.config import scrivi_config, CARTELLE_LISTE, REGISTRAZIONI, leggi_config, QUI
from i18n import _, imposta_lingua, LINGUE
from core.playlists import liste_in_cartella, BUFFER, LOGHI, NOMI_URL, CACHE_LISTE, CHIAVI, copia_lista_url, e_una_lista, _CACHE_PARSED_LOCK, _CACHE_PARSED_MEMORIA
from core.colors import CACHE_LOGHI, leggi_colori, scrivi_colori, colore_di, colore_dal_logo
from core.stream import varianti, chiave_clearkey, server_mpd, CACHE_VARIANTE
from core.constants import (SCALA_FILE, CATEGORIE_URL, VERSIONE, DONA, REPO, UA, FONDO, PANNELLO,
                            BARRA, STATO, TASTO, SCELTO, TESTO, GRIGIO, ACCENTO,
                            CERCA, IN_ONDA, TESTO_ONDA)
from core.discs import dischi, cd_audio, dvd_cifrato, e_dvd, titolo_da_etichetta
from core.recordings import registrazioni, piu_nuova
from core.epg import guide_da_aggiornare, CACHE_EPG, nome_epg
from core.favorites import leggi_preferiti, leggi_preferiti_cat, scrivi_preferiti
import os
import re
import time
import random
import json
import shutil
import hashlib
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen


def _prepara_file_cartella(cartella, elementi, tag_cache):
    risultato = []
    for nome, percorso, ide in elementi:
        estensione = os.path.splitext(percorso)[1][1:].lower()
        if estensione in AUDIO:
            titolo, artista, album, anno = tag_di(percorso, tag_cache)
            if not titolo:
                titolo, artista_file, album_file, anno_file = dal_percorso(percorso, (cartella,))
                artista = artista or artista_file
                album = album or album_file
                anno = anno or anno_file
            nome = titolo or nome
            sotto = " · ".join(x for x in (artista, album, anno) if x)
            categoria = "Music"
        else:
            titolo, anno = titolo_anno(percorso)
            nome = titolo or nome
            sotto = anno or ""
            categoria = "Video"
        risultato.append((nome, percorso, ide, categoria, cartella, sotto))
    risultato.sort(key=lambda voce: str(voce[0]).strip().casefold())
    return risultato


class _DurataFile(QThread):
    completato = Signal(str, object)

    def __init__(self, percorso):
        super().__init__()
        self.percorso = percorso

    def run(self):
        self.completato.emit(self.percorso, durata_di(self.percorso))

class _ScansionaCartelle(QThread):
    completato = Signal(object, str)

    def __init__(self, cartelle, tag_cache):
        super().__init__()
        self.cartelle = list(cartelle)
        self.tag_cache = tag_cache

    def run(self):
        risultati = {}
        try:
            for cartella in self.cartelle:
                risultati[cartella] = _prepara_file_cartella(cartella, media_in(cartella), self.tag_cache)
            self.completato.emit(risultati, "")
        except Exception as errore:
            self.completato.emit(risultati, str(errore))


class _ScansionaCartella(QThread):
    completato = Signal(str, object, str)

    def __init__(self, cartella, tag_cache):
        super().__init__()
        self.cartella = cartella
        self.tag_cache = tag_cache

    def run(self):
        try:
            elementi = media_in(self.cartella)
            preparati = _prepara_file_cartella(self.cartella, elementi, self.tag_cache)
            self.completato.emit(self.cartella, preparati, "")
        except Exception as errore:
            self.completato.emit(self.cartella, [], str(errore))


class _CaricaGuide(QThread):
    completato = Signal(bool)
    errore = Signal(str)

    def __init__(self, sessione, silenzioso=False):
        super().__init__()
        self.sessione = sessione
        self.silenzioso = silenzioso

    def run(self):
        try:
            self.sessione.carica_guide(self.silenzioso)
        except Exception as errore:
            if not self.silenzioso:
                self.errore.emit(str(errore))
        self.completato.emit(self.silenzioso)



class _ScaricaColoreLogo(QThread):
    completato = Signal(str, str)

    def __init__(self, url, logo):
        super().__init__()
        self.url = url
        self.logo = logo

    def run(self):
        try:
            colore = colore_dal_logo(self.logo) or ""
        except Exception:
            colore = ""
        self.completato.emit(self.url, colore)



class _CaricaCopertina(QThread):
    completato = Signal(str)

    def __init__(self, url, destinazione):
        super().__init__()
        self.url = url
        self.destinazione = destinazione

    def run(self):
        try:
            dati = copertina_dentro(self.url)
            if dati:
                os.makedirs(os.path.dirname(self.destinazione), exist_ok=True)
                with open(self.destinazione, "wb") as stream:
                    stream.write(dati)
        except Exception:
            pass
        self.completato.emit(self.url)

class _CaricaFotoArtisti(QThread):
    foto = Signal(str, str)

    def __init__(self, artwork, file_audio, corrente):
        super().__init__()
        self.artwork = artwork
        self.file_audio = list(file_audio)
        self.corrente = corrente

    def _attendi(self, secondi):
        fine = time.monotonic() + secondi
        while time.monotonic() < fine:
            if self.isInterruptionRequested():
                return False
            time.sleep(min(0.1, fine - time.monotonic()))
        return not self.isInterruptionRequested()

    def run(self):
        try:
            if self.corrente in self.file_audio:
                indice = self.file_audio.index(self.corrente)
                self.file_audio = self.file_audio[indice:] + self.file_audio[:indice]
            elif self.corrente:
                self.file_audio.insert(0, self.corrente)
            visti = set()
            richieste = 0
            for percorso in self.file_audio:
                if self.isInterruptionRequested():
                    break
                artista = self.artwork.artista_del_file(percorso)
                chiave = artista.casefold()
                if not artista or chiave in visti:
                    continue
                visti.add(chiave)
                destinazione = self.artwork.percorso_foto(artista)
                if os.path.isfile(destinazione) and os.path.getsize(destinazione) > 0:
                    continue
                foto = self.artwork.scarica_foto(artista)
                if foto:
                    self.foto.emit(artista, foto)
                richieste += 1
                if not self._attendi(2.1):
                    break
                if richieste and richieste % 30 == 0:
                    self.artwork.salva_cache()
                    if not self._attendi(5):
                        break
        except Exception:
            pass
        finally:
            self.artwork.salva_cache()





class _RisolviStream(QThread):
    completato = Signal(str, object, str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            elenco = varianti(self.url)
            self.completato.emit(self.url, elenco, "")
        except Exception as errore:
            self.completato.emit(self.url, [], str(errore))


class _AggiornaListe(QThread):
    completato = Signal(bool)

    def __init__(self, urls):
        super().__init__()
        self.urls = list(urls)

    def run(self):
        cambiata = False
        for url in self.urls:
            percorso = os.path.join(
                CACHE_LISTE, hashlib.md5(url.encode()).hexdigest() + ".m3u")
            try:
                with open(percorso, "rb") as stream:
                    prima = stream.read()
            except OSError:
                prima = None
            try:
                percorso = copia_lista_url(url)
                with open(percorso, "rb") as stream:
                    dopo = stream.read()
                cambiata = cambiata or dopo != prima
            except Exception:
                continue
        self.completato.emit(cambiata)


class _ScaricaCopertine(QThread):
    avanzamento = Signal(int, int)
    completato = Signal(int, int, object, object)

    def __init__(self, file_, chiave, zitto, info, tag_cache, cartelle=(), importati=()):
        super().__init__()
        self.file = None if file_ is None else list(file_)
        self.chiave = chiave
        self.zitto = zitto
        self.info = dict(info or {})
        self.tag_cache = tag_cache
        self.cartelle = list(cartelle)
        self.importati = list(importati)

    def run(self):
        if self.file is None:
            file_ = []
            for cartella in self.cartelle:
                try:
                    file_.extend(voce[1] for voce in media_in(cartella))
                except Exception:
                    continue
            file_.extend(percorso for percorso in self.importati
                         if os.path.isfile(percorso))
        else:
            file_ = self.file
        fatti = nuove = 0
        album_visti = set()
        chiave_tmdb = TMDB_CHIAVE
        lingua = LINGUE_TMDB.get(lingua_corrente(), "en-US")
        provati = leggi_json(FILE_PROVATI)
        if not isinstance(provati, dict):
            provati = {}
        gia_provati = dict(provati)
        try:
            import mutagen
        except ImportError:
            mutagen = None
        for numero, percorso in enumerate(file_, 1):
            if self.isInterruptionRequested():
                break
            if not self.zitto:
                self.avanzamento.emit(numero, len(file_))
            cartella, base = os.path.split(percorso)
            audio = os.path.splitext(percorso)[1][1:].lower() in AUDIO
            voce = cartella if audio else percorso
            if self.zitto and voce in gia_provati:
                continue
            provati[voce] = 1
            radice = os.path.splitext(base)[0]
            try:
                if not audio:
                    if not chiave_tmdb:
                        continue
                    titolo, anno = titolo_anno(percorso)
                    info = info_tmdb(chiave_tmdb, titolo, anno, lingua)
                    if info is None:
                        continue
                    generi = generi_tmdb(chiave_tmdb, lingua, self.info)
                    info["generi"] = [
                        generi.get(str(genere), "") for genere in info.get("generi", [])
                        if generi.get(str(genere))
                    ]
                    self.info[percorso] = info
                    nuove += 1
                    esistenti = [radice + estensione for estensione in
                                 (".jpg", ".jpeg", ".png")] + [
                                     "poster.jpg", "poster.jpeg", "poster.png"]
                    if info.get("poster") and not any(
                            os.path.isfile(os.path.join(cartella, nome))
                            for nome in esistenti):
                        os.makedirs(cartella, exist_ok=True)
                        scarica_in(info["poster"], os.path.join(cartella, radice + ".jpg"))
                        fatti += 1
                else:
                    if mutagen is None:
                        continue
                    tag = mutagen.File(percorso, easy=True)
                    tags = tag.tags if tag is not None and tag.tags else {}
                    prendi = lambda nome: str((tags.get(nome) or [""])[0]).strip()
                    artista = prendi("albumartist") or prendi("artist")
                    album = prendi("album")
                    titolo = prendi("title")
                    anno = prendi("date")[:4]
                    ha_anno = anno.isdigit()
                    if not (artista and album):
                        titolo_file, artista_file, album_file, anno_file = dal_percorso(
                            percorso, self.cartelle)
                        artista = artista or artista_file
                        album = album or album_file
                        titolo = titolo or titolo_file
                        ha_anno = ha_anno or bool(anno_file)
                    if artista and titolo and not album:
                        copertine = [radice + estensione for estensione in
                                     (".jpg", ".jpeg", ".png")]
                        if any(os.path.isfile(os.path.join(cartella, nome))
                               for nome in copertine) or copertina_dentro(percorso) is not None:
                            continue
                        urls, anno_mb, album_mb = copertina_da_brano(artista, titolo)
                        time.sleep(1.1)
                        if album_mb or anno_mb:
                            self.info[percorso] = {"album": album_mb, "anno": anno_mb}
                            nuove += 1
                        for url in urls:
                            try:
                                os.makedirs(cartella, exist_ok=True)
                                scarica_in(url, os.path.join(cartella, radice + ".jpg"))
                                fatti += 1
                                break
                            except Exception:
                                continue
                        continue
                    if cartella in album_visti:
                        continue
                    album_visti.add(cartella)
                    nomi_copertina = [
                        nome + estensione for nome in ("cover", "folder")
                        for estensione in (".jpg", ".jpeg", ".png")
                    ]
                    ha_copertina = any(
                        os.path.isfile(os.path.join(cartella, nome))
                        for nome in nomi_copertina
                    ) or copertina_dentro(percorso) is not None
                    if not (artista and album) or (ha_copertina and ha_anno):
                        continue
                    url, anno_mb = copertina_musicbrainz(artista, album)
                    time.sleep(1.1)
                    if anno_mb and not ha_anno:
                        self.info[cartella] = {"anno": anno_mb}
                        nuove += 1
                    if url and not ha_copertina:
                        os.makedirs(cartella, exist_ok=True)
                        scarica_in(url, os.path.join(cartella, "cover.jpg"))
                        fatti += 1
            except Exception:
                continue
        scrivi_json(FILE_PROVATI, provati)
        if nuove:
            scrivi_json(FILE_INFO, self.info)
        self.completato.emit(fatti, nuove, self.info, self.chiave)


class _VerificaVersione(QThread):
    completato = Signal(str, str)
    errore = Signal(str)

    def run(self):
        try:
            richiesta = Request(
                "https://api.github.com/repos/%s/releases/latest" % REPO,
                headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
            dati = json.loads(urlopen(richiesta, timeout=10).read().decode("utf-8", "ignore"))
            self.completato.emit(str(dati.get("tag_name", "")).lstrip("vV"),
                                 str(dati.get("html_url", "")))
        except Exception as errore:
            self.errore.emit(str(errore))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        imposta_lingua(leggi_config().get("lingua", "en"))
        self.setWindowTitle("XVB v" + VERSIONE)
        self.resize(1280, 720)
        self.setMinimumSize(800, 480)
        self.setAcceptDrops(True)
        self.sessione = Sessione()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(self.sessione.config.get("in_cima")))
        self.ripeti = self.sessione.config.get("ripeti", "")
        self.velocita = 1
        self.shuffle_attivo = bool(self.sessione.config.get("shuffle"))
        self._ordine_vero = None
        self._ordine_shuffle = None
        self.setStyleSheet(
            (
                "QMainWindow,QWidget{background:%s;color:%s}"
                "QMenuBar{background:%s;color:white}"
                "QMenuBar::item:selected,QMenu::item:selected{background:%s}"
                "QMenu{background:%s;color:%s;border:1px solid %s}"
                "QMenu::item{padding:6px 22px}"
                "QPushButton{background:%s;color:%s;border:0;padding:6px}"
                "QPushButton:hover{background:%s;color:white}"
                "QSlider::groove:horizontal{height:4px;background:#4a4a4a}"
                "QSlider::sub-page:horizontal{background:white}"
                "QSlider::handle:horizontal{width:0}"
            ) % (FONDO, TESTO, PANNELLO, SCELTO, PANNELLO, TESTO,
                 SCELTO, TASTO, TESTO, SCELTO)
        )
        self._costruisci_menu()
        centrale = QWidget(self)
        self.setCentralWidget(centrale)
        self._centrale = centrale
        root = QVBoxLayout(centrale)
        self._layout_principale = root
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.contenuto = QWidget(centrale)
        riga = QHBoxLayout(self.contenuto)
        riga.setContentsMargins(0, 0, 0, 0)
        riga.setSpacing(0)

        self.sinistra = QFrame(self.contenuto)
        self.sinistra.setFixedWidth(max(140, int(self.sessione.config.get("larga_sx", 300))))
        sx = QVBoxLayout(self.sinistra)
        sx.setContentsMargins(8, 8, 8, 8)
        sx.setSpacing(6)
        self.root = self
        self.tag_cache = leggi_tag()
        self.artwork_artista = ArtistArtwork(self.tag_cache, self.sessione.config.get("cartelle", []))
        self._artist_worker = None
        self.sottotitoli = {}
        self.colori = leggi_colori()
        self._logo_threads = []
        self._cover_threads = []
        self.info = leggi_json(FILE_INFO)
        self._worker_copertine = None
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        for percorso in self.sessione.config.get("importati", []):
            if not os.path.isfile(percorso) or any(v[1] == percorso for v in self.sessione.canali):
                continue
            estensione = os.path.splitext(percorso)[1][1:].lower()
            if estensione in AUDIO:
                titolo, artista, album, anno = tag_di(percorso, self.tag_cache)
                nome = titolo or os.path.splitext(os.path.basename(percorso))[0]
                self.sottotitoli[percorso] = " · ".join(x for x in (artista, album, anno) if x)
                categoria = "Music"
            else:
                nome, anno = titolo_anno(percorso)
                nome = nome or os.path.splitext(os.path.basename(percorso))[0]
                self.sottotitoli[percorso] = anno or ""
                categoria = "Video"
            self.sessione.canali.append((nome, percorso, None, categoria, "__importati__"))
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]

        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        self._percorso_attivo = None
        self._categoria_attiva = None
        self._registrazioni_attive = []
        self.reg_in_uso = None
        self._durate_cercate = set()
        self._durata_workers = []
        self.cerca = Ricerca(self.sinistra, self._filtra, vuota=_("Search"))
        sx.addWidget(self.cerca)
        self.elenco = Elenco(self.sinistra)
        self.elenco.setContextMenuPolicy(Qt.CustomContextMenu)
        self.elenco.customContextMenuRequested.connect(self._menu_canale)
        self.elenco.singolo = self._seleziona_canale
        self.elenco.itemDoubleClicked.connect(self._apri_selezionato)
        self.elenco.prog_di = self._progresso_di
        sx.addWidget(self.elenco, 1)
        self.nome_in_onda = ""
        self.ide_in_onda = None
        self.file_in_onda = None
        self._riempi_elenco()

        self.video = QWidget(self.contenuto)
        self.video.setMouseTracking(True)
        self.video_layout = QStackedLayout(self.video)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setStackingMode(QStackedLayout.StackAll)
        self.sfondo = Sfondo(self.video)
        self._sfondo_url = None
        self.video_layout.addWidget(self.sfondo)
        self.player_area = QWidget(self.video)
        self.player_area.setStyleSheet("background:transparent")
        self.player_layout = QHBoxLayout(self.player_area)
        self.player_layout.setContentsMargins(0, 0, 0, 0)
        self.player_layout.setSpacing(0)
        self.video_layout.addWidget(self.player_area)
        try:
            self.player = MpvVideo(self.player_area, options=self._mpv_buffer_options())
            self.player_layout.addWidget(self.player, 1)
            self.player.installEventFilter(self)
            self.player.evento.connect(lambda evento, p=self.player: self._evento_player(p, evento))
            self.player.setMouseTracking(True)
        except Exception as errore:
            self.player = None
            avviso = QLabel("libmpv: " + str(errore), self.player_area)
            avviso.setAlignment(Qt.AlignCenter)
            avviso.setStyleSheet("color:#9e9e9e;background:transparent")
            self.player_layout.addWidget(avviso, 1)

        self.destra = QFrame(self.contenuto)
        self.destra.setFixedWidth(max(140, int(self.sessione.config.get("larga_dx", 220))))
        dx = QVBoxLayout(self.destra)
        dx.setContentsMargins(8, 8, 8, 8)
        self.et_liste = QLabel(_("Playlists"), self.destra)
        self.et_liste.setStyleSheet("color:#9e9e9e")
        dx.addWidget(self.et_liste)
        self.el_liste = Sidebar(self.destra)
        self.el_liste.setContextMenuPolicy(Qt.CustomContextMenu)
        self.el_liste.customContextMenuRequested.connect(self._menu_liste)
        self.el_liste.selected.connect(self._scegli_voce_liste)
        dx.addWidget(self.el_liste, 1)
        self._riempi_liste()

        riga.addWidget(self.sinistra)
        self.maniglia_sx = Maniglia(self, self.sinistra, "larga_sx", 1)
        riga.addWidget(self.maniglia_sx)
        riga.addWidget(self.video, 1)
        self.maniglia_dx = Maniglia(self, self.destra, "larga_dx", -1)
        riga.addWidget(self.maniglia_dx)
        riga.addWidget(self.destra)
        root.addWidget(self.contenuto, 1)

        self.barra = QFrame(centrale)
        self.barra.setFixedHeight(96)
        self.barra.installEventFilter(self)
        self._overlay_attivo = False
        self._timer_overlay = QTimer(self)
        self._timer_overlay.setSingleShot(True)
        self._timer_overlay.timeout.connect(self._nascondi_overlay)
        comandi = QVBoxLayout(self.barra)
        comandi.setContentsMargins(12, 38, 12, 0)
        comandi.setSpacing(0)
        self.posizione = QSlider(Qt.Horizontal, self.barra)
        self.posizione.setRange(0, 1000)
        self.posizione.setGeometry(0, 30, self.barra.width(), 10)
        self.posizione.setFixedHeight(10)
        self.posizione.setStyleSheet(
            "QSlider::groove:horizontal{height:2px;background:#4a4a4a}"
            "QSlider::sub-page:horizontal{background:#ffffff}"
            "QSlider::handle:horizontal{width:0;height:0;border:0}")
        self.posizione.sliderReleased.connect(self._seek)
        controlli = QHBoxLayout()
        controlli.setSpacing(4)
        self._pulsanti = {}
        self.tendina = Tendina(self)

        def pulsante(chiave, nome, callback, lato=24, etichetta=None):
            b = QPushButton(self.barra)
            percorso = os.path.join(QUI, "icone", nome + ".png")
            if os.path.isfile(percorso):
                b.setIcon(QIcon(percorso))
                b.setIconSize(QSize(lato, lato))
                b.setFixedSize(lato + 10, lato + 10)
            else:
                b.setText(etichetta or nome)
                b.setFixedSize(max(34, lato + 10), lato + 10)
            b.setToolTip(etichetta or nome)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(callback)
            self._pulsanti[chiave] = b
            controlli.addWidget(b)
            return b

        pulsante("precedente", "prima", lambda: self.salta(-1), 34, _("Previous"))
        pulsante("indietro", "-10", lambda: self.avanza(-10), 24, "-10")
        self.play_button = pulsante("play", "play", self.pausa, 48, _("Play"))
        pulsante("stop", "stop", self.ferma, 34, _("Stop"))
        pulsante("avanti", "+10", lambda: self.avanza(10), 24, "+10")
        pulsante("successivo", "dopo", lambda: self.salta(1), 34, _("Next"))
        pulsante("rec", "rec", self.registra, 24, _("Record"))
        pulsante("repeat", "repeat", self._menu_ripeti, 24, _("Repeat"))
        self.shuffle_button = pulsante("shuffle", "shuffle", lambda: self.mpris_shuffle(not self.shuffle_attivo), 24, _("Shuffle"))
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setStyleSheet("QPushButton:checked{background:%s;border-radius:8px}" % SCELTO)
        controlli.addStretch(1)
        pulsante("favorite", "favorite_off", self._preferito_in_onda, 24, _("Favorite"))
        pulsante("fullscreen", "pieno", self.schermo_intero, 24, _("Fullscreen"))
        pulsante("pip", "pip", self.pip_si_no, 24, "PiP")
        self.speed_button = pulsante("speed", "x1", self.gira_velocita, 24, _("Playback speed"))
        self.speed_button.hide()
        self.b_qualita = pulsante("quality", "setting", self._apri_menu_qualita, 24, _("Quality"))
        self.b_qualita.hide()
        pulsante("sidebar", "playlist", self._sidebar, 24, _("Playlists"))
        self.colore_barra = None
        self.volume = Cursore(
            self.barra, self._volume, larga=85, alta=26, barra=BARRA,
            traccia="#4a4a4a", pieno="#ffffff")
        self.volume.valore = int(self.sessione.config.get("volume", 85))
        self.volume_largo = 0
        self.volume.setMaximumWidth(0)
        controlli.addWidget(self.volume)
        self.b_muto = pulsante("mute", "volume", self._muto, 24, _("Mute"))
        for widget in (self.volume, self.b_muto):
            widget.installEventFilter(self)
        self._timer_volume = QTimer(self)
        self._timer_volume.setSingleShot(True)
        self._timer_volume.timeout.connect(lambda: self.anima_volume(-1))
        comandi.addLayout(controlli)
        root.addWidget(self.barra)

        self.avviso = QFrame(centrale)
        self.avviso.setFixedHeight(42)
        self.avviso.setStyleSheet("QFrame{background:%s}" % ACCENTO)
        avviso_layout = QHBoxLayout(self.avviso)
        avviso_layout.setContentsMargins(12, 0, 12, 0)
        self.et_avviso = QLabel("", self.avviso)
        self.et_avviso.setStyleSheet("color:#17121f")
        avviso_layout.addWidget(self.et_avviso, 1)
        self.avviso.installEventFilter(self)
        self.et_avviso.installEventFilter(self)
        self.avviso.hide()
        self.avviso_chiave = (None, ())
        self._timer_avviso = QTimer(self)
        self._timer_avviso.setSingleShot(True)
        self._timer_avviso.timeout.connect(self.chiudi_avviso)
        root.insertWidget(1, self.avviso)

        stato = QWidget(centrale)
        stato.setFixedHeight(28)
        stato.setStyleSheet("background:#121217")
        stato_layout = QHBoxLayout(stato)
        stato_layout.setContentsMargins(8, 0, 10, 0)
        stato_layout.setSpacing(8)
        self.et_carico = QLabel(stato)
        self.et_carico.setFixedSize(18, 18)
        self.et_carico.hide()
        self._icona_carico = QPixmap(os.path.join(QUI, "icone", "loading.png"))
        self._angolo_carico = 0
        stato_layout.addWidget(self.et_carico)
        self.et_categoria = QLabel(stato)
        self.et_categoria.setStyleSheet("color:#9e9e9e")
        self.et_categoria.hide()
        stato_layout.addWidget(self.et_categoria)
        self.riga_stato = QLabel("XVB", stato)
        self.riga_stato.setStyleSheet("color:#e0e0e0")
        stato_layout.addWidget(self.riga_stato, 1)
        self.et_ora_programma = QLabel(stato)
        self.et_ora_programma.setStyleSheet("color:#9e9e9e")
        self.et_ora_programma.hide()
        stato_layout.addWidget(self.et_ora_programma)
        self.et_prossimo = QLabel(stato)
        self.et_prossimo.setStyleSheet("color:#bdbdbd")
        self.et_prossimo.hide()
        stato_layout.addWidget(self.et_prossimo)
        self.et_ora_prossimo = QLabel(stato)
        self.et_ora_prossimo.setStyleSheet("color:#9e9e9e")
        self.et_ora_prossimo.hide()
        stato_layout.addWidget(self.et_ora_prossimo)
        self._timer_carico = QTimer(self)
        self._timer_carico.setInterval(50)
        self._timer_carico.timeout.connect(self._gira_carico)
        self.orologio = QLabel(time.strftime("%a %d %b  %H:%M"), stato)
        self.orologio.setStyleSheet("color:#e0e0e0")
        stato_layout.addWidget(self.orologio)
        root.addWidget(stato)
        self._timer_orologio = QTimer(self)
        self._timer_orologio.timeout.connect(
            lambda: self.orologio.setText(time.strftime("%a %d %b  %H:%M")))
        self._timer_orologio.start(30000)
        self._timer_info = QTimer(self)
        self._timer_info.timeout.connect(self.aggiorna_info_canale)
        self._timer_info.start(30000)
        self._timer_spegnimento = QTimer(self)
        self._timer_spegnimento.setSingleShot(True)
        self._timer_spegnimento.timeout.connect(self.scade_timer_spegnimento)
        self.timer_fine = None

        self._pieno = False
        self.player2 = None
        self.player_pip = None
        self.pip_window = None
        self._chiudendo_pip = False
        self.split = False
        self.schermo_attivo = 0
        self.registrando = ""
        self.inizio_rec = 0.0
        self.fine_rec = 0.0
        self.piano = None
        self._guida_selezionata = None
        self._timer_rec = QTimer(self)
        self._timer_rec.timeout.connect(self.controlla_registrazione)
        self._timer_rec.start(1000)
        self._dischi_visti = None
        self._timer_dischi = QTimer(self)
        self._timer_dischi.timeout.connect(self.controlla_dischi)
        self._timer_dischi.start(5000)
        self.controlla_dischi()
        self._timer_refresh = QTimer(self)
        self._timer_refresh.timeout.connect(self.aggiorna_periodico)
        self._timer_refresh.start(1800000)
        self._epg_ultima_tentata = time.time()
        self._epg_caricata_il = 0.0
        self._timer_epg = QTimer(self)
        self._timer_epg.timeout.connect(self.controlla_aggiornamento_epg)
        self._timer_epg.start(1800000)
        self._worker_liste = None
        self.mpv = self.player
        self._mpris = avvia_mpris(self)
        self._timer_mpris = QTimer(self)
        self._timer_mpris.timeout.connect(self._aggiorna_mpris)
        if self._mpris is not None:
            self._timer_mpris.start(1000)
        self.nuova = None
        self.pagina_nuova = None
        self._versione_worker = None
        QTimer.singleShot(8000, lambda: self.controlla_versione(zitto=True))
        QTimer.singleShot(8000, self.controlla_copertine)
        self._indice_canale = -1
        self._giro_traccia = 0
        self.fermato = None
        self._eof_gestito = False
        self.salti = 0
        self._ultima_posizione = None
        self.loop_ab_a = None
        self.loop_ab_b = None
        self.loop_ab_file = None
        self.loop_ab_in_corso = False
        self.varianti = []
        self.quale = -1
        self._stream_player = None
        self._stream_workers = []
        self._subtitle_workers = []
        self._finestra_sottotitoli = None
        self._pulsante_download_sub = None
        self.ripeti = self.sessione.config.get("ripeti", "")
        self.shuffle_attivo = bool(self.sessione.config.get("shuffle"))
        self.shuffle_button.setChecked(self.shuffle_attivo)
        self.shuffle_button.setToolTip(_("Shuffle on") if self.shuffle_attivo else _("Shuffle"))
        self._epg_rifare = False
        self._epg_sessione = self.sessione
        self._thread_epg = _CaricaGuide(self._epg_sessione)
        self._thread_epg.completato.connect(self._epg_pronto)
        self._thread_epg.errore.connect(self._epg_errore)
        self._thread_epg.start()
        self._timer_player = QTimer(self)
        self._timer_player.timeout.connect(self._aggiorna_player)
        self._timer_player.start(500)
        self._aggiorna_recenti()
        self.applica_filtri_audio()
        self._volume(self.volume.value())
        self._icona_volume()
        self._aggiorna_icone_ripeti()
        self.applica_uscita_audio(silenzioso=True)
        self.applica_video()
        self.aggiorna_periodico()
        self.elenco.salta = self.salta
        self.elenco.avanza = self.avanza
        self._installa_scorciatoie()
        self._aggiorna_overlay_pannelli()
        QTimer.singleShot(100, self._carica_cartelle_configurate)


    def _carica_cartelle_configurate(self):
        cartelle = [p for p in self.sessione.config.get("cartelle", []) if os.path.isdir(p)]
        if not cartelle:
            return
        worker = _ScansionaCartelle(cartelle, self.tag_cache)
        worker.completato.connect(self._cartelle_configurate_scansionate)
        worker.finished.connect(lambda w=worker: self._rimuovi_worker_scansione(w))
        self.__dict__.setdefault("_scan_workers", []).append(worker)
        worker.start()

    def _cartelle_configurate_scansionate(self, risultati, errore):
        if errore:
            self.riga_stato.setText(_("Some media folders could not be scanned: %s") % errore)
        gia = {voce["percorso"] for voce in self.sessione.liste}
        for cartella, elementi in risultati.items():
            if cartella in gia:
                continue
            locali = self._media_locale(cartella, elementi)
            if not locali:
                continue
            self.sessione.canali.extend(locali)
            self.sessione.liste.append({
                "percorso": cartella, "nome": os.path.basename(cartella),
                "canali": [(n, p, ide) for n, p, ide, _cat, _path in locali],
                "categorie": {p: cat for _n, p, _ide, cat, _path in locali},
            })
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self._riempi_liste()
        self._riempi_elenco()


    def _focus_blocca_tasti(self):
        focus = QApplication.focusWidget()
        if isinstance(focus, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox)):
            return True
        if isinstance(focus, QComboBox) and focus.isEditable():
            return True
        if focus is self.elenco or focus is self.el_liste:
            return True
        if focus is not None and (self.elenco.isAncestorOf(focus) or self.el_liste.isAncestorOf(focus)):
            return True
        return False

    def _installa_scorciatoie(self):
        associazioni = (
            (QKeySequence(Qt.Key_M), self._muto),
            (QKeySequence(Qt.Key_Plus), lambda: self._regola("audio-delay", 0.1)),
            (QKeySequence(Qt.Key_Minus), lambda: self._regola("audio-delay", -0.1)),
            (QKeySequence(Qt.Key_Up), lambda: self.volume.setValue(self.volume.value() + 5)),
            (QKeySequence(Qt.Key_Down), lambda: self.volume.setValue(self.volume.value() - 5)),
            (QKeySequence(Qt.Key_Left), lambda: self.salta(-1)),
            (QKeySequence(Qt.Key_Right), lambda: self.salta(1)),
            (QKeySequence("Shift+Left"), lambda: self.avanza(-10)),
            (QKeySequence("Shift+Right"), lambda: self.avanza(10)),
            (QKeySequence(Qt.Key_PageUp), lambda: self.salta(-1)),
            (QKeySequence(Qt.Key_PageDown), lambda: self.salta(1)),
            (QKeySequence(Qt.Key_F11), self.schermo_intero),
            (QKeySequence(Qt.Key_Escape), self._escape),
        )
        self._scorciatoie = []
        for sequenza, callback in associazioni:
            scorciatoia = QShortcut(sequenza, self)
            scorciatoia.setContext(Qt.WindowShortcut)
            scorciatoia.activated.connect(
                lambda f=callback: None if self._focus_blocca_tasti() else f())
            self._scorciatoie.append(scorciatoia)

    def _escape(self):
        if self.pip_window is not None:
            self.esci_pip()
        elif self.isFullScreen():
            self.schermo_intero()


    def _aggiorna_sfondo(self):
        if not hasattr(self, "sfondo") or self.player is None:
            return
        if self.split:
            self.player.show()
            if self.player2:
                self.player2.show()
            return
        if getattr(self, "_sfondo_forzato", False):
            if self._sfondo_url != "__default__":
                self.sfondo.imposta(dissolvi=True)
                self._sfondo_url = "__default__"
            self.player.hide()
            return
        percorso = self.file_in_onda
        if not percorso:
            if self._sfondo_url != "__default__":
                self.sfondo.imposta(dissolvi=True)
                self._sfondo_url = "__default__"
            self.player.hide()
            return
        solo_audio = os.path.isabs(percorso) and os.path.splitext(percorso)[1][1:].lower() in AUDIO
        if not solo_audio:
            try:
                tracce = self.player.leggi_nodo("track-list") or []
                if tracce:
                    solo_audio = not any(
                        voce.get("type") == "video" and not voce.get("albumart")
                        for voce in tracce if isinstance(voce, dict))
            except Exception:
                pass
        if solo_audio:
            artista = self.artwork_artista.artista_del_file(percorso) if os.path.isabs(percorso) else ""
            foto = self.artwork_artista.percorso_foto(artista) if artista else ""
            dissolvi = self._sfondo_url is not None
            if foto and os.path.isfile(foto) and os.path.getsize(foto) > 0:
                if self._sfondo_url != foto:
                    self.sfondo.imposta(foto, dissolvi=dissolvi)
                    self._sfondo_url = foto
            elif self._sfondo_url != percorso:
                immagine = self.logo_di(percorso)
                if immagine is not None:
                    self.sfondo.imposta_pixmap(immagine, dissolvi=dissolvi)
                else:
                    self.sfondo.imposta(dissolvi=dissolvi)
                self._sfondo_url = percorso
            self.player.hide()
        else:
            if self._sfondo_url != "__default__":
                self.sfondo.imposta()
                self._sfondo_url = "__default__"
            self.player.show()

    def _mostra_carico(self, attivo):
        if attivo and not self._timer_carico.isActive() and not self._icona_carico.isNull():
            self.et_carico.show()
            self._timer_carico.start()
        elif not attivo:
            self._timer_carico.stop()
            self.et_carico.clear()
            self.et_carico.hide()

    def _gira_carico(self):
        if self._icona_carico.isNull():
            self._timer_carico.stop()
            self.et_carico.hide()
            return
        trasformazione = QTransform().rotate(self._angolo_carico)
        icona = self._icona_carico.transformed(trasformazione, Qt.SmoothTransformation)
        self.et_carico.setPixmap(icona.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._angolo_carico = (self._angolo_carico + 20) % 360

    def _aggiorna_player(self):
        self._aggiorna_sfondo()
        player = self._attivo()
        if not player:
            return
        try:
            self._mostra_carico(player.leggi("paused-for-cache") == "yes")
            posizione = player.leggi("time-pos")
            durata = player.leggi("duration")
            if posizione is not None:
                try:
                    posizione_corrente = float(posizione)
                    if self._ultima_posizione is None or posizione_corrente > self._ultima_posizione + 0.25:
                        self.salti = 0
                    self._ultima_posizione = posizione_corrente
                except (TypeError, ValueError):
                    pass
            if posizione and durata and not self.posizione.isSliderDown():
                totale = float(durata)
                if totale > 0:
                    self.posizione.setValue(int(float(posizione) * 1000 / totale))
            if self.file_in_onda and os.path.isabs(self.file_in_onda) and posizione is not None and durata:
                try:
                    pos, totale = float(posizione), float(durata)
                    if totale > 0:
                        cfg = self.sessione.config
                        posizioni = cfg.setdefault("posizioni", {})
                        durate = cfg.setdefault("durate", {})
                        if totale - pos < 20:
                            posizioni.pop(self.file_in_onda, None)
                            durate.pop(self.file_in_onda, None)
                        else:
                            posizioni[self.file_in_onda] = round(pos, 1)
                            durate[self.file_in_onda] = round(totale, 1)
                        if len(posizioni) > 300:
                            for vecchio in list(posizioni)[:len(posizioni) - 300]:
                                posizioni.pop(vecchio, None)
                                durate.pop(vecchio, None)
                        adesso = time.time()
                        if adesso - getattr(self, "_posizione_scritta", 0.0) > 10:
                            self._posizione_scritta = adesso
                            scrivi_config(cfg)
                            self.elenco.ridisegna_colonna()
                except (TypeError, ValueError, OSError):
                    pass
            if posizione and self.loop_ab_file == self.file_in_onda and self.loop_ab_a is not None and self.loop_ab_b is not None:
                if float(posizione) >= self.loop_ab_b and self.loop_ab_in_corso:
                    self.loop_ab_in_corso = False
                    player.seek(self.loop_ab_a)
                elif float(posizione) < self.loop_ab_b:
                    self.loop_ab_in_corso = True
            if player.leggi("eof-reached") == "yes" and not self._eof_gestito:
                self._eof_gestito = True
                if self.file_in_onda and os.path.isabs(self.file_in_onda):
                    self.prossimo_file()
                elif self.ripeti == "tutti":
                    self.salta(1)
        except Exception:
            return



    def cambia_lingua(self, codice):
        imposta_lingua(codice)
        self.sessione.config["lingua"] = codice
        scrivi_config(self.sessione.config)
        self.menuBar().clear()
        self._costruisci_menu()
        self.et_liste.setText(_("Playlists"))
        self.cerca.casella.setPlaceholderText(_("Search"))
        self._aggiorna_recenti()
        if self.avviso.isVisible() and self.avviso_chiave[0]:
            self.et_avviso.setText(_(self.avviso_chiave[0]) % self.avviso_chiave[1])
        self.riga_stato.setText(_("ready"))

    def buffer_attuale(self):
        chiave = self.sessione.config.get("buffer", "standard")
        return next((voce for voce in BUFFER if voce[0] == chiave), BUFFER[2])

    def _mpv_buffer_options(self):
        voce = self.buffer_attuale()
        return {
            "demuxer-max-bytes": str(voce[2] * 1048576),
            "demuxer-max-back-bytes": str(voce[3] * 1048576),
            "demuxer-readahead-secs": str(voce[4]),
            "cache-pause-wait": str(voce[5]),
        }

    def _aggiorna_menu_repeat(self):
        for modalita, azione in self.azioni_repeat.items():
            azione.setChecked(self.ripeti == modalita)

    def _capitoli_disponibili(self):
        player = self._attivo()
        capitoli = player.leggi_nodo("chapter-list") if player else []
        return capitoli if isinstance(capitoli, list) and len(capitoli) >= 2 else []

    def _aggiorna_visibilita_capitoli(self):
        disponibili = bool(self._capitoli_disponibili())
        self.azione_capitolo_precedente.setVisible(disponibili)
        self.azione_capitolo_successivo.setVisible(disponibili)
        self.menu_capitoli.menuAction().setVisible(disponibili)

    def _riempi_menu_capitoli(self):
        menu = self.menu_capitoli
        menu.clear()
        player = self._attivo()
        capitoli = self._capitoli_disponibili()
        if not capitoli:
            return
        try:
            valore = player.leggi("chapter")
            attuale = int(float(valore)) if valore is not None else -1
        except (TypeError, ValueError):
            attuale = -1
        if len(capitoli) <= 99:
            for indice, capitolo in enumerate(capitoli):
                titolo = (capitolo.get("title") or "").strip()
                if not titolo or titolo == "(unnamed)":
                    titolo = _("Chapter %d") % (indice + 1)
                secondi = int(float(capitolo.get("time") or 0))
                ore, resto = divmod(secondi, 3600)
                minuti, secondi = divmod(resto, 60)
                orario = "%02d:%02d:%02d" % (ore, minuti, secondi)
                testo = ("✓  " if indice == attuale else "    ") + titolo + "  ·  " + orario
                menu.addAction(self._azione(
                    testo, lambda _=False, i=indice: self.vai_capitolo(i)))

    def vai_capitolo(self, numero, relativo=False):
        player = self._attivo()
        if not player:
            return
        try:
            if relativo:
                player.comando("add", "chapter", numero)
            else:
                player.imposta("chapter", numero)
        except Exception:
            pass

    def _ciclo_ripeti(self):
        modalita = ("", "uno", "tutti")
        try:
            indice = modalita.index(self.ripeti)
        except ValueError:
            indice = 0
        self.metti_ripeti(modalita[(indice + 1) % len(modalita)])

    def _menu_ripeti(self):
        pulsante = self._pulsanti.get("repeat")
        if pulsante is None:
            return
        posizione = pulsante.mapToGlobal(pulsante.rect().bottomLeft())
        voci = []
        for modalita, etichetta in (
            ("", _("Repeat off")), ("uno", _("Repeat file")),
            ("tutti", _("Repeat playlist"))
        ):
            testo = ("*  " if self.ripeti == modalita else "   ") + etichetta
            voci.append((testo, lambda m=modalita: self.metti_ripeti(m)))
        self.tendina.apri(posizione.x(), posizione.y(), voci,
                          sopra=True, chi=pulsante)

    def _sidebar(self):
        if self.isFullScreen():
            stato = getattr(self, "_sidebar_prima", (True, True))
            mostra = not all(stato)
            self._sidebar_prima = (mostra, mostra)
            return
        mostra = self.sinistra.isHidden() and self.destra.isHidden()
        self.sinistra.setVisible(mostra)
        self.destra.setVisible(mostra)
        self.maniglia_sx.setVisible(mostra)
        self.maniglia_dx.setVisible(mostra)
        self._aggiorna_overlay_pannelli()

    def _nascondi_pannello(self, pannello):
        mostra = not pannello.isVisible()
        pannello.setVisible(mostra)
        if pannello is self.sinistra:
            self.maniglia_sx.setVisible(mostra)
        elif pannello is self.destra:
            self.maniglia_dx.setVisible(mostra)
        if not self.isFullScreen():
            self._aggiorna_overlay_pannelli()

    def _aggiorna_overlay_pannelli(self):
        if self.pip_window is not None:
            self._disattiva_overlay()
            return
        self._attiva_overlay()

    def _aggiorna_menu_view(self):
        self.azione_lista.setText(_("Show list") if self.sinistra.isHidden() else _("Hide list"))
        self.azione_sidebar.setText(_("Show sidebar") if self.destra.isHidden() else _("Hide sidebar"))
        self.azione_top.setChecked(bool(self.sessione.config.get("in_cima")))

    def sempre_in_cima(self):
        attivo = not bool(self.sessione.config.get("in_cima"))
        self.sessione.config["in_cima"] = attivo
        scrivi_config(self.sessione.config)
        visibile = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, attivo)
        if visibile:
            self.show()

    def apri_volume(self):
        self._timer_volume.stop()
        self.anima_volume(1)

    def chiudi_volume_tra_poco(self):
        self._timer_volume.start(400)

    def anima_volume(self, verso):
        passo = max(1, self.volume.larga // 5)
        largo = max(0, min(self.volume.larga, self.volume_largo + verso * passo))
        if largo == self.volume_largo:
            return
        self.volume_largo = largo
        self.volume.setMaximumWidth(largo)
        self.volume.updateGeometry()
        if 0 < largo < self.volume.larga:
            QTimer.singleShot(15, lambda: self.anima_volume(verso))

    def _icona_volume(self):
        pulsante = self._pulsanti.get("mute")
        if pulsante is None:
            return
        muto = bool(getattr(self, "_muto_attivo", False))
        valore = self.volume.get()
        if muto:
            nome, suggerimento = "muto", _("Unmute")
        elif valore == 0:
            nome, suggerimento = "volume_off", _("Mute")
        elif valore < 34:
            nome, suggerimento = "volume_low", _("Mute")
        elif valore < 67:
            nome, suggerimento = "volume", _("Mute")
        else:
            nome, suggerimento = "volume_high", _("Mute")
        percorso = os.path.join(QUI, "icone", nome + ".png")
        if not os.path.isfile(percorso):
            percorso = os.path.join(QUI, "icone", "volume.png")
        if os.path.isfile(percorso):
            pulsante.setIcon(QIcon(percorso))
        pulsante.setToolTip(suggerimento)

    def _muto(self):
        self._muto_attivo = not getattr(self, "_muto_attivo", False)
        self._imposta("mute", "yes" if self._muto_attivo else "no")
        self._icona_volume()

    def metti_buffer(self, chiave):
        voce = next((v for v in BUFFER if v[0] == chiave), None)
        if voce is None:
            return
        self.sessione.config["buffer"] = chiave
        scrivi_config(self.sessione.config)
        for player in (self.player, self.player2):
            if player:
                for nome, valore in (("demuxer-max-bytes", voce[2] * 1048576),
                                     ("demuxer-max-back-bytes", voce[3] * 1048576),
                                     ("demuxer-readahead-secs", voce[4]),
                                     ("cache-pause-wait", voce[5])):
                    try:
                        player.imposta(nome, valore)
                    except Exception:
                        pass
        self.riga_stato.setText("Buffer: " + voce[1])

    def _avvia_scarica_copertine(self, file_, chiave, zitto=False):
        worker = self._worker_copertine
        if worker is not None and worker.isRunning():
            return
        worker = _ScaricaCopertine(
            file_, chiave, zitto, self.info, self.tag_cache,
            self.sessione.config.get("cartelle", []),
            self.sessione.config.get("importati", []))
        worker.avanzamento.connect(self._avanzamento_copertine)
        worker.completato.connect(
            lambda fatti, nuove, info, percorso, w=worker:
            self._copertine_completate(w, fatti, nuove, info, percorso))
        worker.finished.connect(
            lambda w=worker: self._rimuovi_worker_copertine(w))
        self._worker_copertine = worker
        worker.start()

    def controlla_copertine(self):
        importati = self.sessione.config.get("importati", [])
        cartelle = list(self.sessione.config.get("cartelle", []))
        file_importati = [percorso for percorso in importati if os.path.isfile(percorso)]
        if cartelle or file_importati:
            self._avvia_scarica_copertine(None, None, True)

    def scarica_copertine(self):
        if not self._percorso_attivo or not self._canali_visibili:
            self.riga_stato.setText(_("open a folder of films or music first"))
            return
        file_ = [voce[1] for voce in self._canali_visibili if os.path.isabs(voce[1])]
        if not file_:
            self.riga_stato.setText(_("open a folder of films or music first"))
            return
        self._avvia_scarica_copertine(file_, self._percorso_attivo)

    def _avanzamento_copertine(self, numero, totale):
        self.riga_stato.setText(
            _("downloading posters and covers... %d/%d") % (numero, totale))

    def _copertine_completate(self, worker, fatti, nuove, info, percorso):
        self.info = info
        if fatti or not worker.zitto:
            self.riga_stato.setText(_("%d posters and covers downloaded") % fatti)
        if nuove and percorso and self._percorso_attivo == percorso:
            self._riempi_elenco()
        elif fatti and percorso and self._percorso_attivo == percorso:
            self._riempi_elenco()

    def _rimuovi_worker_copertine(self, worker):
        if self._worker_copertine is worker:
            self._worker_copertine = None

    def _azione(self, nome, callback, scorciatoia=None):
        azione = QAction(nome, self)
        if scorciatoia:
            azione.setShortcut(QKeySequence(scorciatoia))
        azione.triggered.connect(callback)
        return azione

    def _costruisci_menu(self):
        media = self.menuBar().addMenu(_("Media"))
        media.addAction(self._azione(_("Open file..."), self.apri_file, "Ctrl+O"))
        media.addAction(self._azione(_("Import files..."), self.importa_file))
        media.addAction(self._azione(_("Open folder..."), self.apri_cartella))
        media.addAction(self._azione(_("Add playlist file..."), self.aggiungi_lista_file))
        media.addAction(self._azione(_("Open URL..."), self.apri_url, "Ctrl+L"))
        media.addAction(self._azione(_("Download posters and covers"), self.scarica_copertine))
        self.menu_recenti = media.addMenu(_("Recent"))
        media.addAction(self._azione(_("Clear recent"), self.pulisci_recenti))
        media.addSeparator()
        media.addAction(self._azione(_("Quit"), self.close, "Ctrl+Q"))
        playback = self.menuBar().addMenu(_("Playback"))
        playback.addAction(self._azione(_("Play / Pause"), self.pausa, "Space"))
        playback.addAction(self._azione(_("Stop"), self.ferma, "S"))
        playback.addAction(self._azione(_("Back 10 s"), lambda: self._comando("seek", "-10", "relative")))
        playback.addAction(self._azione(_("Forward 10 s"), lambda: self._comando("seek", "10", "relative")))
        playback.addSeparator()
        playback.addAction(self._azione(_("Set A-B loop point A"), self.loop_ab_imposta_a))
        playback.addAction(self._azione(_("Set A-B loop point B"), self.loop_ab_imposta_b))
        playback.addAction(self._azione(_("Clear A-B loop"), self.loop_ab_azzera))
        playback.addSeparator()
        playback.addAction(self._azione(_("Previous"), lambda: self.salta(-1)))
        playback.addAction(self._azione(_("Next"), lambda: self.salta(1)))
        self.azione_capitolo_precedente = self._azione(
            _("Previous chapter"), lambda: self.vai_capitolo(-1, relativo=True))
        self.azione_capitolo_successivo = self._azione(
            _("Next chapter"), lambda: self.vai_capitolo(1, relativo=True))
        playback.addAction(self.azione_capitolo_precedente)
        playback.addAction(self.azione_capitolo_successivo)
        self.menu_capitoli = playback.addMenu(_("Chapters"))
        self.menu_capitoli.aboutToShow.connect(self._riempi_menu_capitoli)
        self.azione_capitolo_precedente.setVisible(False)
        self.azione_capitolo_successivo.setVisible(False)
        self.menu_capitoli.menuAction().setVisible(False)
        playback.addSeparator()
        for velocita in (0.5, 0.75, 1, 1.25, 1.5, 2):
            playback.addAction(self._azione("Speed x%g" % velocita,
                                            lambda _=False, v=velocita: self.metti_velocita(v)))
        sleep = playback.addMenu(_("Sleep timer"))
        for minuti in (15, 30, 45, 60, 90, 120):
            sleep.addAction(self._azione(_("%d minutes") % minuti,
                                         lambda _=False, m=minuti: self.imposta_timer_spegnimento(m)))
        sleep.addSeparator()
        sleep.addAction(self._azione(_("Cancel sleep timer"), self.annulla_timer_spegnimento))
        self.azione_shuffle = QAction(_("Shuffle"), self)
        self.azione_shuffle.setCheckable(True)
        self.azione_shuffle.setChecked(self.shuffle_attivo)
        self.azione_shuffle.triggered.connect(self.mpris_shuffle)
        playback.addAction(self.azione_shuffle)
        self.menu_ripeti = playback.addMenu(_("Repeat"))
        self.azioni_ripeti = {}
        for chiave, etichetta in (("", _("Off")), ("uno", _("One")), ("tutti", _("All"))):
            azione = QAction(etichetta, self)
            azione.setCheckable(True)
            azione.triggered.connect(lambda _=False, k=chiave: self.metti_ripeti(k))
            self.menu_ripeti.addAction(azione)
            self.azioni_ripeti[chiave] = azione
        self._aggiorna_azioni_ripeti()
        video = self.menuBar().addMenu(_("Video"))
        for nome, valore in (("Auto", "-1"), ("16:9", "16:9"), ("4:3", "4:3"), ("21:9", "21:9")):
            video.addAction(self._azione("Aspect " + nome,
                                         lambda _=False, v=valore: self.metti_proporzioni(v)))
        video.addAction(self._azione(_("Fill screen (crop)"), self.riempi))
        video.addAction(self._azione(_("Deinterlace"), self.deinterlaccia))
        video.addAction(self._azione(_("Hardware decoding"), self.decodifica_hw))
        video.addSeparator()
        for nome, valore in (("Brightness +", ("brightness", 10)), ("Brightness -", ("brightness", -10)),
                             ("Contrast +", ("contrast", 10)), ("Contrast -", ("contrast", -10)),
                             ("Saturation +", ("saturation", 10)), ("Saturation -", ("saturation", -10))):
            video.addAction(self._azione(nome, lambda _=False, v=valore: self.regola(*v)))
        video.addAction(self._azione(_("Reset picture"), self.azzera_immagine))
        video.addAction(self._azione(_("Screenshot"), lambda: self._comando("screenshot")))
        self.menu_qualita = video.addMenu(_("Quality"))
        self.menu_qualita.setEnabled(False)
        self.menu_qualita.aboutToShow.connect(self._riempi_menu_qualita)
        audio = self.menuBar().addMenu(_("Audio"))
        audio.addAction(self._azione(_("Next audio track"), lambda: self._ciclo("aid")))
        audio.addAction(self._azione(_("Next subtitle track"), lambda: self._ciclo("sid")))
        self.menu_tracce_audio = audio.addMenu(_("Audio tracks"))
        self.menu_tracce_sub = audio.addMenu(_("Subtitles"))
        self.menu_tracce_audio.aboutToShow.connect(lambda: self._riempi_menu_tracce(self.menu_tracce_audio, "audio"))
        self.menu_tracce_sub.aboutToShow.connect(lambda: self._riempi_menu_tracce(self.menu_tracce_sub, "sub"))
        audio.addAction(self._azione(_("Load subtitles..."), self.carica_sottotitoli))
        self.azione_sottotitoli_online = self._azione(
            _("Search subtitles online..."), self.cerca_sottotitoli_online)
        audio.addAction(self.azione_sottotitoli_online)
        audio.aboutToShow.connect(
            lambda: self.azione_sottotitoli_online.setEnabled(bool(self.file_in_onda)))
        audio.addAction(self._azione(_("Audio output device..."), self.scegli_uscita_audio))
        audio.addAction(self._azione(_("Subtitles on/off"), lambda: self._ciclo("sub-visibility")))
        audio.addAction(self._azione("Subtitle delay +100 ms", lambda: self._regola("sub-delay", 0.1)))
        audio.addAction(self._azione("Subtitle delay -100 ms", lambda: self._regola("sub-delay", -0.1)))
        audio.addAction(self._azione(_("Subtitle size +"), lambda: self._regola("sub-scale", 0.1)))
        audio.addAction(self._azione(_("Subtitle size -"), lambda: self._regola("sub-scale", -0.1)))
        audio.addAction(self._azione("Audio delay +100 ms", lambda: self._regola("audio-delay", 0.1)))
        audio.addAction(self._azione("Audio delay -100 ms", lambda: self._regola("audio-delay", -0.1)))
        audio.addSeparator()
        audio.addAction(self._azione(_("Volume boost +50%"), self.boost))
        audio.addAction(self._azione(_("Normalize loudness"), self.normalizza))
        audio.addAction(self._azione(_("Audio equalizer..."), self.equalizzatore_audio))
        iptv = self.menuBar().addMenu(_("IPTV"))
        iptv.addAction(self._azione(_("Add playlist URL"), self.aggiungi_lista_url))
        iptv.addAction(self._azione(_("Open playlists folder"), self.apri_cartella_liste))
        iptv.addAction(self._azione(_("Reload playlists"), self.ricarica_liste))
        iptv.addAction(self._azione(_("Remove selected playlist"), self.rimuovi_lista_selezionata))
        iptv.addSeparator()
        iptv.addAction(self._azione(_("Programme guide"), self.apri_guida))
        iptv.addAction(self._azione(_("Add guide URL"), self.aggiungi_epg_url))
        iptv.addAction(self._azione(_("Reload guide"), self.ricarica_epg_manuale))
        iptv.addAction(self._azione(_("Remove selected guide"), self.togli_epg_selezionata))
        iptv.addSeparator()
        iptv.addAction(self._azione(_("Record now / Stop recording"), self.registra))
        iptv.addAction(self._azione(_("Schedule..."), self.pianifica))
        iptv.addAction(self._azione(_("Cancel schedule"), self.annulla_piano))
        iptv.addAction(self._azione(_("Open recordings folder"), self.apri_registrazioni))
        view = self.menuBar().addMenu(_("View"))
        view.addAction(self._azione(_("Fullscreen"), self.schermo_intero, "F"))
        view.addAction(self._azione(_("Picture in picture"), self.pip_si_no))
        view.addAction(self._azione(_("Split screen"), self.split_si_no, "F2"))
        self.azione_top = self._azione(_("Always on top"), self.sempre_in_cima)
        self.azione_top.setCheckable(True)
        view.addAction(self.azione_top)
        view.addSeparator()
        self.azione_lista = self._azione(_("Hide list"), lambda: self._nascondi_pannello(self.sinistra))
        self.azione_sidebar = self._azione(_("Hide sidebar"), lambda: self._nascondi_pannello(self.destra))
        view.addAction(self.azione_lista)
        view.addAction(self.azione_sidebar)
        view.aboutToShow.connect(self._aggiorna_menu_view)
        lingua = view.addMenu(_("Language"))
        for codice, nome in LINGUE:
            lingua.addAction(self._azione(nome, lambda _=False, c=codice: self.cambia_lingua(c)))
        buffer_menu = view.addMenu(_("Buffer"))
        for chiave, etichetta, *_resto in BUFFER:
            buffer_menu.addAction(self._azione(etichetta, lambda _=False, k=chiave: self.metti_buffer(k)))
        help_menu = self.menuBar().addMenu(_("Help"))
        help_menu.addAction(self._azione(_("About XVB"), self.informazioni))
        self.azione_download = self._azione(_("Up to date"), self.apri_release)
        self.azione_download.setEnabled(False)
        help_menu.addAction(self.azione_download)
        help_menu.addAction(self._azione(_("Check for updates"), self.controlla_versione))
        help_menu.addSeparator()
        help_menu.addAction(self._azione(_("Donate"), self.dona))




    def _attivo(self):
        return self.player2 if self.split and self.schermo_attivo == 1 and self.player2 else self.player

    def _comando(self, *argomenti):
        player = self._attivo()
        if player:
            player.comando(*argomenti)

    def _imposta(self, nome, valore):
        player = self._attivo()
        if player:
            player.imposta(nome, valore)

    def _ciclo(self, nome):
        player = self._attivo()
        if player:
            player.ciclo(nome)

    def _ciclo_valori(self, nome, *valori):
        player = self._attivo()
        if player:
            player.comando("cycle-values", nome, *valori)

    def metti_proporzioni(self, valore):
        self.sessione.config["proporzioni"] = valore
        self.sessione.config["riempi"] = False
        scrivi_config(self.sessione.config)
        self.applica_video()

    def riempi(self):
        self.sessione.config["riempi"] = not bool(self.sessione.config.get("riempi"))
        scrivi_config(self.sessione.config)
        self.applica_video()

    def deinterlaccia(self):
        attivo = not bool(self.sessione.config.get("deinterlaccia"))
        self.sessione.config["deinterlaccia"] = attivo
        scrivi_config(self.sessione.config)
        self.applica_video()

    def decodifica_hw(self):
        attivo = not bool(self.sessione.config.get("hwdec", True))
        self.sessione.config["hwdec"] = attivo
        scrivi_config(self.sessione.config)
        self.applica_video()

    def regola(self, cosa, di):
        valore = max(-100, min(100, int(self.sessione.config.get(cosa, 0)) + di))
        self.sessione.config[cosa] = valore
        scrivi_config(self.sessione.config)
        self.applica_video()
        self._messaggio_temporaneo("%s %+d" % (_(cosa), valore))

    def _regola(self, nome, valore):
        player = self._attivo()
        if player:
            player.regola(nome, valore)

    def azzera_immagine(self):
        for cosa in ("brightness", "contrast", "saturation"):
            self.sessione.config.pop(cosa, None)
        scrivi_config(self.sessione.config)
        self.applica_video()

    def _azzera_video(self):
        self.azzera_immagine()

    def applica_video(self):
        player = self._attivo()
        if player:
            try:
                player.imposta("video-aspect-override",
                               self.sessione.config.get("proporzioni", "-1"))
                player.imposta("panscan", 1.0 if self.sessione.config.get("riempi") else 0.0)
                player.imposta("deinterlace", "yes" if self.sessione.config.get("deinterlaccia") else "no")
                for cosa in ("brightness", "contrast", "saturation"):
                    player.imposta(cosa, int(self.sessione.config.get(cosa, 0)))
            except Exception:
                pass
            hw = "auto-safe" if self.sessione.config.get("hwdec", True) else "no"
            if getattr(self, "_hwdec_messo", None) != hw:
                try:
                    player.imposta("hwdec", hw)
                    self._hwdec_messo = hw
                except Exception:
                    pass
        self.applica_filtri_audio()
        if hasattr(self, "volume"):
            self._volume(self.volume.get())


    def _chiedi_testo(self, titolo, etichetta, valore="", maschera=False):
        def corpo(widget):
            testo = QLabel(etichetta, widget)
            testo.setStyleSheet("color:#9e9e9e")
            widget.contenuto.addWidget(testo)
        finestra = Finestrella(self, titolo, corpo, chiedi=etichetta,
                               valore=valore, larga=460, maschera=maschera)
        return finestra.risposta if finestra.exec() == QDialog.Accepted else None


    def aggiorna_periodico(self):
        if self._worker_liste is not None and self._worker_liste.isRunning():
            return
        self._worker_liste = _AggiornaListe(self.sessione.config.get("liste_url", {}).keys())
        self._worker_liste.completato.connect(self._liste_auto_pronte)
        self._worker_liste.start()

    def _liste_auto_pronte(self, cambiata):
        if cambiata:
            self.ricarica_liste(forza=False)


    def _menu_liste(self, posizione):
        item = self.el_liste.itemAt(posizione)
        if item is None:
            return
        iid = item.data(0, Qt.UserRole)
        valore = self.el_liste.item(str(iid), "valore") if iid is not None else None
        menu = QMenu(self)
        if valore and valore[0] == "__url__":
            url = valore[1]
            menu.addAction(_("Rename..."), lambda: self.rinomina_url(url))
            menu.addAction(_("Set cover..."), lambda: self.metti_copertina(url))
            if os.path.isfile(copertina_url(url)):
                menu.addAction(_("Remove cover"), lambda: self.togli_copertina(url))
            sposta = menu.addMenu(_("Move to"))
            for chiave, etichetta in CATEGORIE_URL + ((None, "Temporary"),):
                sposta.addAction(_(etichetta), lambda _=False, k=chiave, u=url: self.sposta_url(u, k))
            menu.addAction(_("Remove URL"), lambda: self.rimuovi_url(url))
        elif valore and valore[0] == "__epg__":
            menu.addAction(_("Remove guide"), lambda: self.togli_epg(valore[1]))
        elif valore and valore[0] == "__imported_file__":
            menu.addAction(_("Set cover..."), lambda: self.metti_copertina(valore[1]))
            if os.path.isfile(copertina_url(valore[1])):
                menu.addAction(_("Remove cover"), lambda: self.togli_copertina(valore[1]))
            menu.addAction(_("Remove from library"), lambda: self.rimuovi_importato(valore[1]))
        elif valore and valore[0] == "__media_folder__" and valore[1] in self.sessione.config.get("cartelle", []):
            menu.addAction(_("Remove media folder"), lambda: self.rimuovi_cartella_media(valore[1]))
        elif valore and isinstance(valore[0], str) and valore[0].startswith(("http://", "https://")):
            menu.addAction(_("Rename..."), lambda: self.rinomina_lista(valore[0]))
            menu.addAction(_("Remove playlist"), lambda: self.rimuovi_lista(valore[0]))
        elif valore and os.path.isfile(str(valore[0])):
            menu.addAction(_("Rename..."), lambda: self.rinomina_lista(valore[0]))
            menu.addAction(_("Remove from list"), lambda: self.rimuovi_lista(valore[0]))
        if menu.actions():
            menu.exec(self.el_liste.mapToGlobal(posizione))



    def rimuovi_importato(self, percorso):
        self.sessione.config["importati"] = [
            p for p in self.sessione.config.get("importati", []) if p != percorso]
        scrivi_config(self.sessione.config)
        self.sessione.canali = [v for v in self.sessione.canali
                                if not (v[4] == "__importati__" and v[1] == percorso)]
        self.sottotitoli.pop(percorso, None)
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self._riempi_liste()
        self._riempi_elenco()

    def rimuovi_cartella_media(self, cartella):
        cfg = self.sessione.config
        cfg["cartelle"] = [p for p in cfg.get("cartelle", []) if p != cartella]
        scrivi_config(cfg)
        self.sessione.canali = [v for v in self.sessione.canali if v[4] != cartella]
        self.sessione.liste = [v for v in self.sessione.liste if v["percorso"] != cartella]
        self.sottotitoli = {p: v for p, v in self.sottotitoli.items()
                            if not (p == cartella or p.startswith(cartella + os.sep))}
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self._percorso_attivo = None
        self._categoria_attiva = None
        self._riempi_liste()
        self._riempi_elenco()


    def rinomina_lista(self, percorso):
        nome = self._chiedi_testo(_("Rename..."), _("Name:"),
                                 self.sessione.config.get("liste_url", {}).get(
                                     percorso, self.sessione.config.get("nomi_liste", {}).get(
                                         percorso, os.path.basename(percorso))))
        if nome is None or not nome.strip():
            return
        if percorso in self.sessione.config.get("liste_url", {}):
            self.sessione.config["liste_url"][percorso] = nome.strip()
        else:
            self.sessione.config.setdefault("nomi_liste", {})[percorso] = nome.strip()
        scrivi_config(self.sessione.config)
        self.ricarica_liste(forza=False)

    def rimuovi_lista_selezionata(self):
        if self._percorso_attivo:
            self.rimuovi_lista(self._percorso_attivo)

    def rimuovi_lista(self, percorso):
        cfg = self.sessione.config
        if percorso in cfg.get("liste_url", {}):
            cfg["liste_url"].pop(percorso, None)
        elif percorso in cfg.get("liste", []):
            cfg["liste"] = [p for p in cfg["liste"] if p != percorso]
        else:
            return
        scrivi_config(cfg)
        self._percorso_attivo = None
        self._categoria_attiva = None
        self.ricarica_liste(forza=False)


    def aggiungi_lista_file(self):
        percorso, _ = QFileDialog.getOpenFileName(
            self, _("Choose a playlist"), self.sessione.config.get("ultima_cartella", ""),
            "Playlists (*.m3u *.m3u8 *.txt)")
        if not percorso:
            return
        if not e_una_lista(percorso):
            QMessageBox.warning(self, "XVB", _("%s does not look like an M3U playlist") % os.path.basename(percorso))
            return
        liste = self.sessione.config.setdefault("liste", [])
        if percorso not in liste:
            liste.append(percorso)
        self.sessione.config["ultima_cartella"] = os.path.dirname(percorso)
        scrivi_config(self.sessione.config)
        self.ricarica_liste(forza=False)

    def aggiungi_lista_url(self):
        url = self._chiedi_testo(_("Add playlist URL"), _("URL of the playlist (m3u):"))
        if not url or not url.strip():
            return
        url = url.strip()
        liste_url = self.sessione.config.setdefault("liste_url", {})
        if url in liste_url:
            self.riga_stato.setText(_("%s is already there") % NOMI_URL.get(url, url))
            return
        base = os.path.basename(urlparse(url).path.rstrip("/"))
        base = re.sub(r"\.(m3u8?|txt)$", "", base, flags=re.I) or "playlist"
        nome = self._chiedi_testo(_("Add URL"), _("Name:"), base)
        if not nome or not nome.strip():
            return
        liste_url[url] = nome.strip()
        scrivi_config(self.sessione.config)
        self.ricarica_liste(scegli=url)

    def ricarica_liste(self, scegli=None, forza=True):
        precedente = self.sessione
        NOMI_URL.clear()
        NOMI_URL.update(precedente.config.get("nomi_liste", {}))
        NOMI_URL.update(precedente.config.get("liste_url", {}))
        if forza:
            with _CACHE_PARSED_LOCK:
                _CACHE_PARSED_MEMORIA.clear()
            LOGHI.clear()
            CHIAVI.clear()
            self.colori = {}
            scrivi_colori(self.colori)
            for url in precedente.config.get("liste_url", {}):
                try:
                    copia_lista_url(url, "forza")
                except Exception:
                    pass
        nuova = Sessione()
        nuova.epg = precedente.epg
        nuova.epg_nomi = precedente.epg_nomi
        for lista in precedente.liste:
            if lista["percorso"].startswith(("http://", "https://")):
                continue
            if os.path.isdir(lista["percorso"]):
                nuovi = [voce for voce in precedente.canali
                         if voce[4] == lista["percorso"]]
                if nuovi:
                    nuova.canali.extend(nuovi)
                    nuova.liste.append(lista)
        self.sessione = nuova
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in nuova.canali]
        self.epg = nuova.epg
        self.epg_nomi = nuova.epg_nomi
        self._percorso_attivo = scegli if scegli else None
        self._categoria_attiva = None
        self._riempi_liste()
        self._riempi_elenco()
        self.riga_stato.setText("%d channels" % len(self.sessione.canali))

    def apri_cartella_liste(self):
        percorso = CARTELLE_LISTE[0]
        os.makedirs(percorso, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(percorso))

    def aggiungi_epg_url(self):
        url = self._chiedi_testo(_("Add guide URL"), "URL")
        if not url or not url.strip():
            return
        cfg = self.sessione.config
        guide = cfg.get("epg", [])
        if isinstance(guide, str):
            guide = [guide] if guide else []
        if url.strip() not in guide:
            guide.append(url.strip())
        cfg["epg"] = guide
        scrivi_config(cfg)
        self.ricarica_guida()

    def _epg_pronto(self, silenzioso=False):
        self.sessione.epg = self._epg_sessione.epg
        self.sessione.epg_nomi = self._epg_sessione.epg_nomi
        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        if not silenzioso:
            self.riga_stato.setText("EPG ready")
        self._epg_caricata_il = time.time()
        self.aggiorna_info_canale()
        if self._epg_rifare:
            self._epg_rifare = False
            self.ricarica_guida()

    def _epg_errore(self, errore):
        self.riga_stato.setText("EPG: " + errore)


    def nome_guida(self, dove):
        return (self.sessione.config.get("epg_nomi_utente", {}).get(dove)
                or self.sessione.config.get("epg_nomi", {}).get(dove)
                or nome_epg(dove))

    def togli_epg_selezionata(self):
        if self._guida_selezionata:
            self.togli_epg(self._guida_selezionata)

    def togli_epg(self, dove):
        nome = self.nome_guida(dove)
        self.sessione.config["epg"] = [
            d for d in self.sessione.config.get("epg", []) if d != dove]
        self.sessione.config.get("epg_nomi", {}).pop(dove, None)
        self.sessione.config.get("epg_nomi_utente", {}).pop(dove, None)
        scrivi_config(self.sessione.config)
        self._guida_selezionata = None
        self.ricarica_guida()
        self._riempi_liste()
        self.riga_stato.setText(_("removed %s") % nome)

    def ricarica_epg_manuale(self):
        for dove in self.sessione.config.get("epg", []):
            if os.path.isfile(dove):
                continue
            percorso = os.path.join(CACHE_EPG, hashlib.md5(dove.encode()).hexdigest())
            try:
                os.remove(percorso)
            except OSError:
                pass
        self.ricarica_guida()

    def controlla_aggiornamento_epg(self):
        percorsi = self.sessione.config.get("epg", [])
        if isinstance(percorsi, str):
            percorsi = [percorsi] if percorsi else []
        if self._thread_epg.isRunning():
            return
        if guide_da_aggiornare(percorsi, self._epg_caricata_il, self._epg_ultima_tentata):
            self.ricarica_guida(silenzioso=True)

    def ricarica_guida(self, silenzioso=False):
        self._epg_ultima_tentata = time.time()
        if self._thread_epg.isRunning():
            self._epg_rifare = True
            return
        self._epg_sessione = self.sessione
        self._thread_epg = _CaricaGuide(self._epg_sessione, silenzioso)
        self._thread_epg.completato.connect(self._epg_pronto)
        self._thread_epg.errore.connect(self._epg_errore)
        self._thread_epg.start()

    def apri_guida(self):
        if not self.epg:
            self.riga_stato.setText("EPG data not available")
            return
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        finestra = getattr(self, "_finestra_guida", None)
        if finestra is not None:
            try:
                finestra.showNormal()
                finestra.raise_()
                finestra.activateWindow()
                return
            except RuntimeError:
                self._finestra_guida = None
        finestra = Guida(self)
        finestra.setAttribute(Qt.WA_DeleteOnClose, True)
        finestra.destroyed.connect(lambda *_: setattr(self, "_finestra_guida", None))
        self._finestra_guida = finestra
        finestra.show()


    def metti_copertina(self, dove):
        percorso, _ = QFileDialog.getOpenFileName(
            self, _("Choose cover"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not percorso:
            return
        destinazione = copertina_url(dove)
        try:
            os.makedirs(os.path.dirname(destinazione), exist_ok=True)
            shutil.copy2(percorso, destinazione)
            self._riempi_elenco()
            self.riga_stato.setText(_("Cover saved"))
        except Exception as errore:
            self.riga_stato.setText(_("Cover error: %s") % errore)

    def togli_copertina(self, dove):
        try:
            os.remove(copertina_url(dove))
        except OSError:
            pass
        self._riempi_elenco()

    def _tinta_barra(self, y):
        if not self.colore_barra:
            return BARRA
        colore = QColor(self.colore_barra)
        base = QColor(BARRA)
        altezza = max(1, self.barra.height())
        t = 0.22 * max(0.0, 1.0 - y / float(altezza)) ** 1.6
        return QColor(
            int(base.red() + (colore.red() - base.red()) * t),
            int(base.green() + (colore.green() - base.green()) * t),
            int(base.blue() + (colore.blue() - base.blue()) * t)
        ).name()

    def _stile_barra(self):
        if not self.colore_barra:
            return "QFrame{background:rgba(28,27,34,220)}" if self._overlay_attivo else "QFrame{background:%s}" % BARRA
        cima = QColor(self._tinta_barra(0))
        fondo = QColor(BARRA)
        alfa = 220 if self._overlay_attivo else 255
        return ("QFrame{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 rgba(%d,%d,%d,%d),stop:1 rgba(%d,%d,%d,%d))}" %
                (cima.red(), cima.green(), cima.blue(), alfa,
                 fondo.red(), fondo.green(), fondo.blue(), alfa))

    def colora_stato(self, colore):
        self.colore_barra = colore
        self.barra.setStyleSheet(self._stile_barra())
        if colore:
            self.posizione.setStyleSheet(
                "QSlider::groove:horizontal{height:2px;background:#4a4a4a}"
                "QSlider::sub-page:horizontal{background:%s}"
                "QSlider::handle:horizontal{width:0;height:0;border:0}" % colore)
            self.volume.sfondo(self._tinta_barra)
        else:
            self.posizione.setStyleSheet(
                "QSlider::groove:horizontal{height:2px;background:#4a4a4a}"
                "QSlider::sub-page:horizontal{background:#ffffff}"
                "QSlider::handle:horizontal{width:0;height:0;border:0}")
            self.volume.sfondo(None)

    def colore_canale(self, nome, url):
        if url.startswith(REGISTRAZIONI + os.sep):
            return colore_di(os.path.basename(os.path.dirname(url)))
        if os.path.isabs(url):
            try:
                posizione = next(i for i, voce in enumerate(self.sessione.canali) if voce[1] == url)
            except StopIteration:
                posizione = 0
            return SCALA_FILE[posizione % len(SCALA_FILE)]
        return (self.sessione.config.get("colori_canali", {}).get(url)
                or self.colori.get(url) or colore_di(nome))

    def apri_canale_guida(self, nome, url, ide=None):
        self.apri(url, nome=nome, ide=ide)



    def controlla_dischi(self):
        presenti = (tuple(dischi()), tuple(cd_audio()))
        precedente = self._dischi_visti
        if precedente is not None and presenti != precedente:
            montati = {p for p, _ in presenti[0]}
            rimossi = {p for p, _ in precedente[0]} - montati
            if (self.file_in_onda == "dvd://" and not any(e_dvd(p) for p, _ in presenti[0])):
                self.ferma()
            elif self.file_in_onda == "cdda://" and not presenti[1]:
                self.ferma()
            elif self.file_in_onda and os.path.isabs(self.file_in_onda):
                if any(self.file_in_onda.startswith(p + os.sep) for p in rimossi):
                    self.ferma()
        if presenti != self._dischi_visti:
            self._dischi_visti = presenti
            if hasattr(self, "el_liste"):
                self._riempi_liste()

    def apri_dvd(self, dispositivo):
        player = self._attivo()
        if not player:
            return
        try:
            player.imposta("dvd-device", dispositivo)
            self.apri("dvd://", nome=titolo_da_etichetta(os.path.basename(dispositivo)))
        except Exception as errore:
            self.riga_stato.setText("DVD: " + str(errore))

    def apri_cd(self, dispositivo):
        player = self._attivo()
        if not player:
            return
        try:
            player.imposta("cdda-device", dispositivo)
            player.imposta("cdda-span-a", 1)
            player.imposta("cdda-span-b", 1)
            self.apri("cdda://", nome=_("Audio CD"))
        except Exception as errore:
            self.riga_stato.setText("CD: " + str(errore))

    def apri_disco_dati(self, mountpoint):
        if any(v["percorso"] == mountpoint for v in self.sessione.liste):
            self._percorso_attivo, self._categoria_attiva = mountpoint, None
            self._riempi_elenco()
            return
        nuovi = self._media_locale(mountpoint)
        if not nuovi:
            self.riga_stato.setText(_("No media files found"))
            return
        self.sessione.canali.extend(nuovi)
        self.sessione.liste.append({
            "percorso": mountpoint, "nome": titolo_da_etichetta(os.path.basename(mountpoint)),
            "canali": [(n, p, ide) for n, p, ide, _cat, _path in nuovi],
            "categorie": {p: cat for _n, p, _ide, cat, _path in nuovi},
        })
        self._percorso_attivo, self._categoria_attiva = mountpoint, None
        self._riempi_liste()
        self._riempi_elenco()

    def _riempi_liste(self):
        self.el_liste.clear()
        supporti = dischi()
        cd_presenti = cd_audio()
        dischi_root = None
        if supporti or cd_presenti:
            dischi_root = self.el_liste.insert(
                "", "end", iid="dischi", text=" " + _("Discs"), open=True)
        for indice, (punto, etichetta) in enumerate(supporti):
            if e_dvd(punto):
                if not dvd_cifrato(punto):
                    iid = "dvd:%d" % indice
                    self.el_liste.insert(dischi_root, "end", iid=iid, text=" DVD · " + titolo_da_etichetta(etichetta))
                    self.el_liste.item(iid, valore=("__dvd__", punto))
            else:
                iid = "data:%d" % indice
                self.el_liste.insert(dischi_root, "end", iid=iid, text=" " + titolo_da_etichetta(etichetta))
                self.el_liste.item(iid, valore=("__data__", punto))
        for indice, (dispositivo, tracce) in enumerate(cd_presenti):
            iid = "cd:%d" % indice
            self.el_liste.insert(dischi_root, "end", iid=iid, text=" CD Audio · %d tracks" % tracce)
            self.el_liste.item(iid, valore=("__cd__", dispositivo))
        iptv = self.el_liste.insert("", "end", iid="iptv", text=" IPTV",
                                    image=QPixmap(os.path.join(QUI, "icone", "tv.png")), open=True)
        self.el_liste.item(iptv, valore=("__iptv__", None))
        guide_config = self.sessione.config.get("epg", [])
        if isinstance(guide_config, str):
            guide_config = [guide_config] if guide_config else []
        epg = self.el_liste.insert(iptv, "end", iid="epg",
                                   text=" EPG (%d)" % len(guide_config),
                                   open=bool(guide_config))
        self.el_liste.item(epg, valore=("__epg_folder__", None))
        for indice, guida in enumerate(guide_config):
            iid = "epg:%d" % indice
            self.el_liste.insert(epg, "end", iid=iid,
                                 text=" " + os.path.basename(str(guida)))
            self.el_liste.item(iid, valore=("__epg__", guida))
        m3u = self.el_liste.insert(iptv, "end", iid="m3u",
                                   text=" M3U (%d)" % sum(1 for v in self.sessione.liste if not os.path.isdir(v["percorso"])),
                                   open=True)
        self.el_liste.item(m3u, valore=("__m3u__", None))
        gruppi_m3u = {}
        for indice, lista in enumerate(self.sessione.liste):
            percorso = lista["percorso"]
            if os.path.isdir(percorso):
                continue
            padre = m3u
            if lista.get("gruppo"):
                nome_gruppo = lista["gruppo"]
                if nome_gruppo not in gruppi_m3u:
                    gruppi_m3u[nome_gruppo] = self.el_liste.insert(
                        m3u, "end", iid="gruppo:" + nome_gruppo,
                        text=" " + nome_gruppo, open=True)
                padre = gruppi_m3u[nome_gruppo]
            iid = "lista:%d" % indice
            self.el_liste.insert(padre, "end", iid=iid, text=" " + lista["nome"],
                                 image=QPixmap(os.path.join(QUI, "icone", "player.png")))
            self.el_liste.item(iid, valore=(percorso, None))
            categorie = sorted(set(lista["categorie"].values()), key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = iid + ":cat:%d" % j
                self.el_liste.insert(iid, "end", iid=figlio, text=" " + categoria)
                self.el_liste.item(figlio, valore=(percorso, categoria))
        raccolte = registrazioni()
        if raccolte:
            registrazioni_root = self.el_liste.insert(
                "", "end", iid="registrazioni",
                text=" " + _("Recordings"),
                image=QPixmap(os.path.join(QUI, "icone", "vhs.png")),
                open=False)
            for indice, ((canale, giorno), file_registrati) in enumerate(raccolte):
                try:
                    data = time.strftime("%d/%m/%Y", time.strptime(giorno, "%Y-%m-%d"))
                except ValueError:
                    data = giorno
                gruppo = self.el_liste.insert(
                    registrazioni_root, "end", iid="registrazioni:%d" % indice,
                    text=" %s · %s" % (canale, data))
                self.el_liste.item("registrazioni:%d" % indice,
                                   valore=("__recordings_group__", (canale, giorno)))
                for j, (ora, titolo, percorso) in enumerate(file_registrati):
                    estensione = os.path.splitext(percorso)[1].lower()
                    icona = "music" if estensione == ".mka" else "player"
                    iid = "registrazione:%d:%d" % (indice, j)
                    self.el_liste.insert(
                        gruppo, "end", iid=iid,
                        text=" %s  %s" % (ora, titolo),
                        image=QPixmap(os.path.join(QUI, "icone", icona + ".png")))
                    self.el_liste.item(iid, valore=("__recording__", percorso))
        locale = self.el_liste.insert("", "end", iid="locale",
                                      text=" Local", open=True)
        self.el_liste.item(locale, valore=("__local__", None))
        montati = {p for p, _nome in dischi()}
        for indice, lista in enumerate(self.sessione.liste):
            percorso = lista["percorso"]
            if not os.path.isdir(percorso) or percorso in montati:
                continue
            canali_cartella = [v for v in self.sessione.canali if v[4] == percorso]
            iid = "media:%d" % indice
            self.el_liste.insert(locale, "end", iid=iid,
                                 text=" " + lista["nome"] + " (%d)" % len(canali_cartella),
                                 image=QPixmap(os.path.join(QUI, "icone", "player.png")), open=True)
            self.el_liste.item(iid, valore=("__media_folder__", percorso))
            try:
                sottocartelle = sorted(os.listdir(percorso), key=str.casefold)
            except OSError:
                sottocartelle = []
            for j, nome_sotto in enumerate(sottocartelle):
                sotto = os.path.join(percorso, nome_sotto)
                if nome_sotto.startswith(".") or not os.path.isdir(sotto):
                    continue
                dentro = [v for v in canali_cartella if v[1].startswith(sotto + os.sep)]
                if not dentro:
                    continue
                iid_sotto = iid + ":" + str(j)
                self.el_liste.insert(iid, "end", iid=iid_sotto,
                                     text=" " + nome_sotto + " (%d)" % len(dentro))
                self.el_liste.item(iid_sotto, valore=("__media_folder__", sotto))
        importati = [v for v in self.sessione.canali if v[4] == "__importati__"]
        if importati:
            nodo_importati = self.el_liste.insert(
                locale, "end", iid="importati", text=" " + _("Imported media") +
                " (%d)" % len(importati), open=False)
            self.el_liste.item(nodo_importati, valore=("__importati__", None))
            for i, (nome, percorso, _ide, categoria, _lista) in enumerate(importati):
                iid = "importato:%d" % i
                icona = "music" if categoria == "Music" else "player"
                self.el_liste.insert(nodo_importati, "end", iid=iid, text=" " + nome,
                                     image=QPixmap(os.path.join(QUI, "icone", icona + ".png")))
                self.el_liste.item(iid, valore=("__imported_file__", percorso))
        if self.sessione.preferiti_musica:
            nodo = self.el_liste.insert(locale, "end", iid="preferiti:music", text=" " + _("Music favorites"), open=True)
            for i, (nome, url, ide, categoria) in enumerate(self.sessione.preferiti_musica):
                iid = "preferiti:music:%d" % i
                self.el_liste.insert(nodo, "end", iid=iid, text=" " + nome)
                self.el_liste.item(iid, valore=("__favorite_music__", categoria))
        if self.sessione.preferiti_video:
            nodo = self.el_liste.insert(locale, "end", iid="preferiti:video", text=" " + _("Video favorites"), open=True)
            for i, (nome, url, ide, categoria) in enumerate(self.sessione.preferiti_video):
                iid = "preferiti:video:%d" % i
                self.el_liste.insert(nodo, "end", iid=iid, text=" " + nome)
                self.el_liste.item(iid, valore=("__favorite_video__", categoria))
        if self.sessione.preferiti:
            preferiti = self.el_liste.insert(
                "", "end", iid="preferiti", text=" " + _("Favorites"), open=True)
            categorie = sorted(
                {voce[3] or "MyPlaylist" for voce in self.sessione.preferiti},
                key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = self.el_liste.insert(
                    preferiti, "end", iid="preferiti:%d" % j,
                    text=" " + categoria)
                self.el_liste.item(figlio, valore=("__favorite__", categoria))
        self.el_liste.item(iptv, valore=("__iptv__", None))
        self.el_liste.item(epg, valore=("__epg_folder__", None))
        self.el_liste.item(m3u, valore=("__m3u__", None))
        self.el_liste.item(locale, valore=("__local__", None))

    def _scegli_voce_liste(self, item, _colonna=0):
        dati = self.el_liste.item(item, "valore") if isinstance(item, str) else item.data(0, Qt.UserRole)
        if not dati:
            return
        self._percorso_attivo, self._categoria_attiva = dati
        if self._percorso_attivo == "__imported_file__":
            self.apri(self._categoria_attiva, nome=os.path.basename(self._categoria_attiva))
            return
        if self._percorso_attivo == "__url_cat__":
            self._percorso_attivo = "__url__"
            self._riempi_elenco()
            return
        if self._percorso_attivo == "__url__":
            self.apri_url_da(self._categoria_attiva)
            return
        if self._percorso_attivo == "__url_root__":
            self._percorso_attivo = "__url__"
            self._categoria_attiva = None
            self._riempi_elenco()
            return
        if self._percorso_attivo == "__epg_folder__":
            self.apri_guida()
            return
        if self._percorso_attivo == "__media_folder__":
            self._cartella_media_attiva = self._categoria_attiva
            self._categoria_attiva = None
            self._riempi_elenco()
            return
        if self._percorso_attivo == "__epg__":
            self._guida_selezionata = self._categoria_attiva
            self.riga_stato.setText(self.nome_guida(self._guida_selezionata))
            return
        if self._percorso_attivo == "__recordings_group__":
            self.mostra_registrazioni(self._categoria_attiva)
            return
        if self._percorso_attivo == "__recording__":
            self.apri(self._categoria_attiva, nome=os.path.basename(self._categoria_attiva))
            return
        if self._percorso_attivo == "__dvd__":
            self.apri_dvd(self._categoria_attiva)
            return
        if self._percorso_attivo == "__cd__":
            self.apri_cd(self._categoria_attiva)
            return
        if self._percorso_attivo == "__data__":
            self.apri_disco_dati(self._categoria_attiva)
            return
        self._riempi_elenco()

    def _filtra(self, *_):
        self._riempi_elenco()

    def cerca_durata(self, percorso):
        if percorso in self._durate_cercate:
            return
        self._durate_cercate.add(percorso)
        worker = _DurataFile(percorso)
        worker.completato.connect(self._durata_pronta)
        worker.finished.connect(lambda w=worker: self._rimuovi_worker_durata(w))
        self._durata_workers.append(worker)
        worker.start()

    def _durata_pronta(self, percorso, durata):
        if not durata:
            return
        self.sessione.config.setdefault("durate", {})[percorso] = round(float(durata), 1)
        scrivi_config(self.sessione.config)
        self.elenco.ridisegna_colonna()

    def _rimuovi_worker_durata(self, worker):
        if worker in self._durata_workers:
            self._durata_workers.remove(worker)
        worker.deleteLater()

    def mostra_registrazioni(self, chiave):
        chiave = tuple(chiave)
        voci = dict(registrazioni()).get(chiave, [])
        self.reg_in_uso = chiave
        self._percorso_attivo = "__recordings__"
        self._categoria_attiva = None
        self._registrazioni_attive = [
            (titolo, percorso, None, ora, "__recordings__")
            for ora, titolo, percorso in voci
        ]
        for ora, _titolo, percorso in voci:
            self.sottotitoli[percorso] = ora
        self._riempi_elenco()
        self.riga_stato.setText(_("%s - %d recordings") % (
            "%s %s" % chiave, len(voci)))

    def _riempi_elenco(self):
        if not hasattr(self, "elenco"):
            return
        percorso = self._percorso_attivo
        categoria = self._categoria_attiva
        ricerca = self.cerca.get() if hasattr(self, "cerca") else ""
        self.elenco.delete(*self.elenco.get_children())
        if percorso == "__url__":
            base = [(self.nome_di_url(url), url, None, categoria or "Temporary", "__url__")
                    for url in self.url_di(categoria)]
        elif percorso == "__importati__":
            base = [voce for voce in self.sessione.canali if voce[4] == "__importati__"]
        elif percorso == "__recordings__":
            base = self._registrazioni_attive
        elif percorso == "__media_folder__":
            cartella = getattr(self, "_cartella_media_attiva", "")
            base = [voce for voce in self.sessione.canali
                    if voce[4] == cartella or voce[1].startswith(cartella.rstrip(os.sep) + os.sep)]
        else:
            base = self.sessione.canali
        self._canali_visibili = [voce for voce in base
                                 if (percorso is None or percorso in ("__media_folder__", "__url__")
                                     or voce[4] == percorso
                                     or (percorso == "__local__" and os.path.isdir(voce[4]))
                                     or (percorso in ("__iptv__", "__m3u__")
                                         and not os.path.isdir(voce[4])
                                         and voce[4] not in ("__favorite__", "__favorite_music__", "__favorite_video__")))
                                 and (categoria is None or voce[3] == categoria)
                                 and (not ricerca or ricerca.casefold() in (voce[0] + " " + self.sottotitoli.get(voce[1], "") + " " + voce[1]).casefold())]
        percorsi_visibili = {voce[1] for voce in self._canali_visibili}
        if self._ordine_shuffle and not percorsi_visibili.intersection(self._ordine_shuffle):
            self._ordine_shuffle = None
            self._ordine_vero = None
        if self.shuffle_attivo and self._canali_visibili and not self._ordine_shuffle:
            if all(os.path.isabs(voce[1]) for voce in self._canali_visibili):
                self._ordine_vero = list(self._canali_visibili)
                mischiati = list(self._canali_visibili)
                random.shuffle(mischiati)
                in_onda = [v for v in mischiati if v[1] == self.file_in_onda]
                mischiati = in_onda + [v for v in mischiati if v[1] != self.file_in_onda]
                self._ordine_shuffle = [v[1] for v in mischiati]
        if self.shuffle_attivo and self._ordine_shuffle:
            ordine = {percorso: i for i, percorso in enumerate(self._ordine_shuffle)}
            self._canali_visibili.sort(key=lambda voce: ordine.get(voce[1], len(ordine)))
        for i, voce in enumerate(self._canali_visibili):
            nome, url, ide, gruppo, _lista = voce
            sotto = self.sottotitoli.get(url) or gruppo
            self.elenco.insert("", "end", iid=str(i), text=nome + "\n" + sotto,
                               colore=self.colore_canale(nome, url), logo=self.logo_di(url),
                               tags=("onda",) if url == self.file_in_onda else ())

    def _segna_in_onda(self):
        if not hasattr(self, "elenco"):
            return
        for iid in self.elenco.get_children():
            dati = self.elenco.item(iid)
            tags = tuple(tag for tag in dati.get("tags", ()) if tag != "onda")
            try:
                voce = self._canali_visibili[int(iid)]
            except (ValueError, IndexError, TypeError):
                voce = None
            if voce is not None and voce[1] == self.file_in_onda:
                tags += ("onda",)
            if tags != tuple(dati.get("tags", ())):
                self.elenco.item(iid, tags=tags)

    def _seleziona_canale(self):
        selezione = self.elenco.selection()
        if not selezione:
            return
        voce = self._canali_visibili[int(selezione[0])]
        self._indice_canale = int(selezione[0])
        self.riga_stato.setText(voce[0])
        self.apri(voce[1], nome=voce[0], ide=voce[2])

    def _apri_selezionato(self, _item=None):
        selezione = self.elenco.selection()
        if selezione:
            voce = self._canali_visibili[int(selezione[0])]
            self._indice_canale = int(selezione[0])
            self.apri(voce[1], nome=voce[0], ide=voce[2])




    def colore_canale(self, nome, url):
        if url.startswith(REGISTRAZIONI + os.sep):
            return colore_di(os.path.basename(os.path.dirname(url)))
        if os.path.isabs(url):
            try:
                posizione = next(i for i, voce in enumerate(self.sessione.canali) if voce[1] == url)
            except StopIteration:
                posizione = 0
            return SCALA_FILE[posizione % len(SCALA_FILE)]
        return (self.sessione.config.get("colori_canali", {}).get(url)
                or self.colori.get(url) or colore_di(nome))

    def logo_di(self, url):
        if os.path.isabs(url):
            copertina = copertina_url(url)
            if os.path.isfile(copertina):
                pix = QPixmap(copertina)
                return pix if not pix.isNull() else None
            estensione = os.path.splitext(url)[1][1:].lower()
            if estensione in AUDIO:
                percorso = copertina_url(url)
                if os.path.isfile(percorso):
                    pix = QPixmap(percorso)
                    return pix if not pix.isNull() else None
                if not any(w.url == url and w.isRunning() for w in self._cover_threads):
                    worker = _CaricaCopertina(url, percorso)
                    worker.completato.connect(self._copertina_pronta)
                    worker.finished.connect(lambda w=worker: self._rimuovi_worker_copertina(w))
                    self._cover_threads.append(worker)
                    worker.start()
                return None
            poster = poster_film(url)
            return QPixmap(poster) if poster else None
        copertina = copertina_url(url)
        if os.path.isfile(copertina):
            pix = QPixmap(copertina)
            return pix if not pix.isNull() else None
        logo = LOGHI.get(url)
        if not logo:
            return None
        import hashlib
        percorso = os.path.join(CACHE_LOGHI, hashlib.md5(logo.encode()).hexdigest())
        if os.path.isfile(percorso) and os.path.getsize(percorso):
            pix = QPixmap(percorso)
            return pix if not pix.isNull() else None
        if not any(w.url == url and w.isRunning() for w in self._logo_threads):
            worker = _ScaricaColoreLogo(url, logo)
            worker.completato.connect(self._logo_pronto)
            worker.finished.connect(lambda w=worker: self._rimuovi_worker_logo(w))
            self._logo_threads.append(worker)
            worker.start()
        return None


    def _rimuovi_worker_copertina(self, worker):
        if worker in self._cover_threads:
            self._cover_threads.remove(worker)

    def _copertina_pronta(self, _url):
        if hasattr(self, "elenco"):
            self._riempi_elenco()
        self._sfondo_url = None
        self._aggiorna_sfondo()

    def _richiedi_foto_artisti(self, corrente):
        self.artwork_artista.radici = list(self.sessione.config.get("cartelle", []))
        worker = self._artist_worker
        if worker is not None and worker.isRunning():
            return
        file_audio = [voce[1] for voce in self.sessione.canali
                      if os.path.isabs(voce[1])
                      and os.path.splitext(voce[1])[1][1:].lower() in AUDIO]
        worker = _CaricaFotoArtisti(self.artwork_artista, file_audio, corrente)
        self._artist_worker = worker
        worker.foto.connect(self._foto_artista_pronta)
        worker.start()

    def _foto_artista_pronta(self, artista, percorso):
        corrente = self.file_in_onda or ""
        if not (corrente and os.path.isabs(corrente)
                and os.path.splitext(corrente)[1][1:].lower() in AUDIO):
            return
        if self.artwork_artista.artista_del_file(corrente).casefold() != artista.casefold():
            return
        if os.path.isfile(percorso):
            self.sfondo.imposta(percorso, dissolvi=True)
            self._sfondo_url = percorso
            if self.player:
                self.player.hide()

    def _rimuovi_worker_logo(self, worker):
        if worker in self._logo_threads:
            self._logo_threads.remove(worker)

    def _logo_pronto(self, url, colore):
        if colore:
            self.colori[url] = colore
            scrivi_colori(self.colori)
        if hasattr(self, "elenco"):
            self._riempi_elenco()
        if getattr(self, "_finestra_guida", None):
            self._finestra_guida.ridisegna()


    def _tipo_preferito(self, voce):
        return tipo_preferiti(voce[1])

    def _voce_preferibile_in_onda(self):
        url = self.file_in_onda
        if not url or not self.nome_in_onda:
            return None
        voce = next((v for v in self.sessione.canali
                     if v[1] == url and v[4] not in (
                         "__favorite__", "__favorite_music__", "__favorite_video__")), None)
        if voce is None and os.path.isabs(url) and e_media(url):
            estensione = os.path.splitext(url)[1][1:].lower()
            categoria = "Music" if estensione in AUDIO else "Video"
            voce = (self.nome_in_onda, url, self.ide_in_onda, categoria, "__importati__")
        return voce

    def _preferito_in_onda(self):
        voce = self._voce_preferibile_in_onda()
        if voce is None:
            return
        url = voce[1]
        tipo = self._tipo_preferito(voce)
        if any(v[1] == url for v in leggi_preferiti(tipo)):
            self.rimuovi_preferito(url, tipo)
        else:
            self.aggiungi_preferito(voce, tipo)
        self._icona_preferito()

    def _icona_preferito(self):
        pulsante = self._pulsanti.get("favorite")
        if pulsante is None:
            return
        voce = self._voce_preferibile_in_onda()
        possibile = voce is not None
        pulsante.setVisible(possibile)
        if possibile:
            tipo = self._tipo_preferito(voce)
            acceso = any(v[1] == voce[1] for v in leggi_preferiti(tipo))
            nome = "favorite_on" if acceso else "favorite_off"
            percorso = os.path.join(QUI, "icone", nome + ".png")
            if os.path.isfile(percorso):
                pulsante.setIcon(QIcon(percorso))

    def _menu_canale(self, posizione):
        item = self.elenco.itemAt(posizione)
        if item is None:
            return
        indice = self.elenco.row(item)
        self.elenco.selection_set(str(indice))
        if not 0 <= indice < len(self._canali_visibili):
            return
        voce = self._canali_visibili[indice]
        tipo = self._tipo_preferito(voce)
        if tipo == PREF_IPTV:
            preferiti = self.sessione.preferiti
        elif tipo == PREF_MUSICA:
            preferiti = self.sessione.preferiti_musica
        else:
            preferiti = self.sessione.preferiti_video
        gia = any(v[1] == voce[1] for v in preferiti)
        menu = QMenu(self)
        if gia:
            menu.addAction(_("Remove from favorites"), lambda: self.rimuovi_preferito(voce[1], tipo))
        else:
            menu.addAction(_("Add to favorites"), lambda: self.aggiungi_preferito(voce, tipo))
        menu.exec(self.elenco.mapToGlobal(posizione))

    def aggiungi_preferito(self, voce, tipo=None):
        nome, url, ide, categoria, _lista = voce
        tipo = tipo or self._tipo_preferito(voce)
        preferiti = leggi_preferiti(tipo)
        if any(v[1] == url for v in preferiti):
            return
        preferiti.append((nome, url, ide, categoria))
        scrivi_preferiti(preferiti, tipo)
        self._ricarica_preferiti()
        self.riga_stato.setText(_("Added to favorites"))

    def rimuovi_preferito(self, url, tipo=None):
        tipi = [tipo] if tipo else [PREF_IPTV, PREF_MUSICA, PREF_VIDEO]
        for t in tipi:
            preferiti = [v for v in leggi_preferiti(t) if v[1] != url]
            scrivi_preferiti(preferiti, t)
        self._ricarica_preferiti()
        self.riga_stato.setText(_("Removed from favorites"))

    def _ricarica_preferiti(self):
        self.sessione.preferiti = leggi_preferiti_cat(PREF_IPTV)
        self.sessione.preferiti_musica = leggi_preferiti_cat(PREF_MUSICA)
        self.sessione.preferiti_video = leggi_preferiti_cat(PREF_VIDEO)
        self._ricostruisci_canali_preferiti()
        self._riempi_liste()
        self._riempi_elenco()

    def _ricostruisci_canali_preferiti(self):
        self.sessione.canali = [v for v in self.sessione.canali
                                if v[4] not in ("__favorite__", "__favorite_music__", "__favorite_video__")]
        for nome, url, ide, categoria in self.sessione.preferiti:
            self.sessione.canali.append((nome, url, ide, categoria or "MyPlaylist", "__favorite__"))
        for nome, url, ide, categoria in self.sessione.preferiti_musica:
            self.sessione.canali.append((nome, url, ide, categoria or "Music", "__favorite_music__"))
        for nome, url, ide, categoria in self.sessione.preferiti_video:
            self.sessione.canali.append((nome, url, ide, categoria or "Video", "__favorite_video__"))
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]

    def _progresso_di(self, iid):
        try:
            voce = self._canali_visibili[int(iid)]
            nome, url, ide = voce[:3]
            if os.path.isabs(url):
                posizioni = self.sessione.config.get("posizioni", {})
                durate = self.sessione.config.get("durate", {})
                posizione = posizioni.get(url)
                durata = durate.get(url)
                if posizione is not None and durata:
                    return max(0.0, min(1.0, float(posizione) / float(durata)))
                if posizione is not None and not durata:
                    self.cerca_durata(url)
                return None
            chiave = ide if ide and ide in self.sessione.epg else self.sessione.epg_nomi.get(
                __import__("core.epg", fromlist=["nome_piatto"]).nome_piatto(nome))
            if not chiave:
                return None
            adesso = time.time()
            for inizio, fine, _titolo in self.sessione.epg.get(chiave, []):
                if inizio <= adesso < fine:
                    return (adesso - inizio) / float(max(1, fine - inizio))
        except Exception:
            return None
        return None

    def _media_locale(self, cartella, elementi=None):
        gia = {voce[1] for voce in self.sessione.canali}
        preparati = (_prepara_file_cartella(cartella, media_in(cartella), self.tag_cache)
                     if elementi is None else elementi)
        nuovi = []
        for nome, percorso, ide, categoria, _origine, sotto in preparati:
            if percorso in gia:
                continue
            self.sottotitoli[percorso] = sotto
            nuovi.append((nome, percorso, ide, categoria, cartella))
        return nuovi

    def apri_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, _("Open folder"))
        if not cartella:
            return
        workers = self.__dict__.setdefault("_scan_workers", [])
        if any(w.cartella == cartella and w.isRunning() for w in workers):
            return
        self.riga_stato.setText(_("Loading %s...") % os.path.basename(cartella.rstrip(os.sep)))
        worker = _ScansionaCartella(cartella, self.tag_cache)
        worker.completato.connect(self._cartella_scansionata)
        worker.finished.connect(lambda w=worker: self._rimuovi_worker_scansione(w))
        workers.append(worker)
        worker.start()

    def _rimuovi_worker_scansione(self, worker):
        workers = self.__dict__.setdefault("_scan_workers", [])
        if worker in workers:
            workers.remove(worker)
        worker.deleteLater()

    def _cartella_scansionata(self, cartella, elementi, errore):
        if errore:
            self.riga_stato.setText(_("Unable to open folder: %s") % errore)
            return
        nuovi = self._media_locale(cartella, elementi)
        if not nuovi:
            self.riga_stato.setText(_("No media files found"))
            return
        self.sessione.canali.extend(nuovi)
        cartelle = self.sessione.config.setdefault("cartelle", [])
        if cartella not in cartelle:
            cartelle.append(cartella)
            scrivi_config(self.sessione.config)
        self.canali.extend((n, p, i) for n, p, i, _c, _l in nuovi)
        self.sessione.liste.append({
            "percorso": cartella, "nome": os.path.basename(cartella),
            "canali": [(n, p, i) for n, p, i, _c, _l in nuovi],
            "categorie": {p: categoria for _n, p, _i, categoria, _l in nuovi},
        })
        self._riempi_liste()
        self._percorso_attivo, self._categoria_attiva = cartella, None
        self._riempi_elenco()
        self.riga_stato.setText(_("%d media files") % len(nuovi))

    def informazioni(self):
        QMessageBox.about(self, "XVB", _("XVB Player 4.4.4"))




    def tracce(self, tipo):
        player = self._attivo()
        if not player:
            return []
        try:
            valore = player.leggi("track-list")
            elenco = json.loads(valore) if valore else []
            return [traccia for traccia in elenco if traccia.get("type") == tipo]
        except Exception:
            return []

    @staticmethod
    def nome_traccia(traccia):
        nome = traccia.get("title") or traccia.get("lang") or ""
        codec = traccia.get("codec") or ""
        return ("%s (%s)" % (nome, codec) if nome and codec
                else nome or codec or str(traccia.get("id")))

    def _riempi_menu_tracce(self, menu, tipo):
        menu.clear()
        tracce = self.tracce(tipo)
        if tipo == "sub":
            attiva = any(traccia.get("selected") for traccia in tracce)
            menu.addAction(self._azione(
                ("   " if attiva else "✓  ") + _("Subtitles off"),
                lambda: self.metti_traccia("sid", "no")))
            if tracce:
                menu.addSeparator()
        if not tracce:
            if tipo == "audio":
                azione = menu.addAction(_("No tracks available"))
                azione.setEnabled(False)
            return
        proprieta = "aid" if tipo == "audio" else "sid"
        for traccia in tracce:
            testo = self.nome_traccia(traccia)
            if traccia.get("selected"):
                testo = "✓  " + testo
            menu.addAction(self._azione(
                testo, lambda _=False, i=traccia.get("id"): self.metti_traccia(proprieta, i)))

    def metti_traccia(self, proprieta, identificativo):
        player = self._attivo()
        if player:
            player.imposta(proprieta, identificativo)

    def cerca_sottotitoli_online(self):
        if not self.file_in_onda:
            self._messaggio_temporaneo(_("nothing is playing"))
            return
        percorso_credenziali = os.path.expanduser("~/.config/xvb/opensubtitles.json")
        try:
            with open(percorso_credenziali, "r", encoding="utf-8") as stream:
                credenziali = json.load(stream)
            if not isinstance(credenziali, dict):
                raise ValueError("Formato credenziali non valido")
        except FileNotFoundError:
            credenziali = {}
        except Exception:
            self._messaggio_temporaneo(_("Unable to read OpenSubtitles credentials"))
            return
        api_key = str(credenziali.get("api_key", "") or "").strip()
        username = str(credenziali.get("username", "") or "").strip()
        password = str(credenziali.get("password", "") or "")
        if not api_key:
            api_key = self._chiedi_testo(
                _("OpenSubtitles API key"), _("Enter your OpenSubtitles API key:"))
            if not api_key or not api_key.strip():
                return
            api_key = api_key.strip()
        if not username:
            username = self._chiedi_testo(
                _("OpenSubtitles username"), _("Enter your OpenSubtitles username:"))
            if not username or not username.strip():
                return
            username = username.strip()
        if not password:
            password = self._chiedi_testo(
                _("OpenSubtitles password"), _("Enter your OpenSubtitles password:"),
                maschera=True)
            if not password:
                return
        credenziali = {"api_key": api_key, "username": username, "password": password}
        try:
            os.makedirs(os.path.dirname(percorso_credenziali), exist_ok=True)
            with open(percorso_credenziali, "w", encoding="utf-8") as stream:
                json.dump(credenziali, stream, indent=2)
            os.chmod(percorso_credenziali, 0o600)
            with open(percorso_credenziali, "r", encoding="utf-8") as stream:
                if json.load(stream) != credenziali:
                    raise ValueError("Verifica del salvataggio fallita")
        except Exception:
            self._messaggio_temporaneo(_("Unable to save OpenSubtitles credentials"))
            return
        lingue = self._chiedi_testo(
            _("Subtitle languages"),
            _("Language codes separated by commas (example: it,en):"), "it,en")
        if not lingue or not lingue.strip():
            return
        media = str(self.file_in_onda)
        percorso = urlparse(media).path if "://" in media else media
        titolo = os.path.splitext(os.path.basename(percorso))[0]
        titolo = re.sub(r"[._]+", " ", titolo).strip() or media
        codici = []
        for codice in lingue.split(","):
            codice = codice.strip().lower()
            if re.fullmatch(r"[a-z]{2,3}", codice) and codice not in codici:
                codici.append(codice)
        if not codici:
            self._messaggio_temporaneo(_("Invalid subtitle language codes"))
            return
        worker = RicercaSottotitoli(api_key, username, password, titolo, ",".join(codici))
        worker.completato.connect(
            lambda chiave, token, risultati, base, t=titolo:
            self._mostra_risultati_sottotitoli(chiave, token, base, risultati, t))
        worker.errore.connect(
            lambda errore: self._messaggio_temporaneo(
                _("Online subtitle search failed: %s") % errore))
        worker.finished.connect(lambda w=worker: self._rimuovi_worker_sottotitoli(w))
        self._subtitle_workers.append(worker)
        self._messaggio_temporaneo(_("Searching online subtitles..."))
        worker.start()

    def _mostra_risultati_sottotitoli(self, api_key, token, base_url, risultati, titolo):
        if not risultati:
            self._messaggio_temporaneo(_("No online subtitles found"))
            return
        finestra = QDialog(self)
        finestra.setWindowTitle(_("Online subtitles"))
        finestra.resize(760, 390)
        finestra.setModal(True)
        finestra.setStyleSheet(
            "QDialog{background:%s;color:%s}"
            "QListWidget{background:%s;color:%s;border:0}"
            "QListWidget::item:selected{background:%s;color:#17121f}"
            "QPushButton{background:%s;color:%s;border:0;padding:6px 14px}"
            "QPushButton:hover{background:%s;color:white}" %
            (PANNELLO, TESTO, IN_ONDA, TESTO, ACCENTO, IN_ONDA, TESTO, SCELTO))
        layout = QVBoxLayout(finestra)
        layout.addWidget(QLabel(_("Choose a subtitle to download"), finestra))
        lista = QListWidget(finestra)
        layout.addWidget(lista, 1)
        validi = []
        for elemento in risultati:
            attributi = elemento.get("attributes") or {}
            files = attributi.get("files") or []
            file_id = next((f.get("file_id") for f in files if f.get("file_id") is not None), None)
            if file_id is None:
                continue
            lingua = attributi.get("language", "?")
            release = attributi.get("release") or (files[0].get("file_name", "") if files else "")
            uploader = (attributi.get("uploader") or {}).get("name", "")
            downloads = attributi.get("download_count", 0)
            riga = "%s  |  %s  |  %s  |  %s %s" % (
                lingua, release or _("Unknown release"),
                uploader or _("Unknown uploader"), downloads, _("downloads"))
            lista.addItem(riga)
            validi.append((file_id, lingua, release))
        if not validi:
            finestra.deleteLater()
            self._messaggio_temporaneo(_("No downloadable subtitles found"))
            return
        lista.setCurrentRow(0)
        fondo = QHBoxLayout()
        fondo.addStretch(1)
        annulla = QPushButton(_("Cancel"), finestra)
        scarica = QPushButton(_("Download and load"), finestra)
        fondo.addWidget(annulla)
        fondo.addWidget(scarica)
        layout.addLayout(fondo)
        self._finestra_sottotitoli = finestra
        self._pulsante_download_sub = scarica

        def avvia_download():
            indice = lista.currentRow()
            if not 0 <= indice < len(validi):
                return
            file_id, lingua, _release = validi[indice]
            scarica.setEnabled(False)
            worker = ScaricaSottotitolo(api_key, token, base_url, file_id, lingua, titolo)
            worker.completato.connect(
                lambda percorso, w=finestra: self._attiva_sottotitolo_online(percorso, w))
            worker.errore.connect(
                lambda errore, w=finestra: self._errore_download_sottotitolo(errore, w))
            worker.finished.connect(lambda w=worker: self._rimuovi_worker_sottotitoli(w))
            self._subtitle_workers.append(worker)
            self._messaggio_temporaneo(_("Downloading subtitle..."))
            worker.start()

        scarica.clicked.connect(avvia_download)
        lista.itemDoubleClicked.connect(lambda _item: avvia_download())
        annulla.clicked.connect(finestra.reject)
        finestra.exec()
        self._finestra_sottotitoli = None
        self._pulsante_download_sub = None

    def _attiva_sottotitolo_online(self, percorso, finestra):
        player = self._attivo()
        try:
            if player is None:
                raise RuntimeError(_("libmpv not available"))
            player.comando("sub-add", percorso, "select")
            self._messaggio_temporaneo(_("subtitles: %s") % os.path.basename(percorso))
            finestra.accept()
        except Exception as errore:
            self._messaggio_temporaneo(
                _("cannot read %s: %s") % (os.path.basename(percorso), errore))

    def _errore_download_sottotitolo(self, messaggio, finestra):
        self._messaggio_temporaneo(_("Subtitle download failed: %s") % messaggio)
        if self._pulsante_download_sub is not None:
            self._pulsante_download_sub.setEnabled(True)

    def _rimuovi_worker_sottotitoli(self, worker):
        if worker in self._subtitle_workers:
            self._subtitle_workers.remove(worker)

    def carica_sottotitoli(self):
        percorso, _ = QFileDialog.getOpenFileName(
            self, _("Load subtitles"), "", "Subtitles (*.srt *.ass *.ssa *.sub *.vtt *.idx *.sup)")
        if percorso:
            self._comando("sub-add", percorso, "select")

    def boost(self):
        attivo = not bool(self.sessione.config.get("boost"))
        self.sessione.config["boost"] = attivo
        scrivi_config(self.sessione.config)
        self._volume(self.volume.value())

    def normalizza(self):
        attivo = not bool(self.sessione.config.get("normalizza"))
        self.sessione.config["normalizza"] = attivo
        scrivi_config(self.sessione.config)
        self.applica_filtri_audio()

    def applica_filtri_audio(self):
        filtri = []
        if self.sessione.config.get("normalizza"):
            filtri.append("dynaudnorm=f=150:g=15")
        bande = self.sessione.config.get("eq_bande", [0] * 10)
        if not isinstance(bande, list) or len(bande) != 10:
            bande = [0] * 10
        for frequenza, guadagno in zip((31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000), bande):
            guadagno = max(-12, min(12, int(guadagno)))
            if guadagno:
                filtri.append("equalizer=f=%d:width_type=o:width=1:g=%d" % (frequenza, guadagno))
        player = self._attivo()
        if player:
            player.imposta("af", "lavfi=[" + ",".join(filtri) + "]" if filtri else "")

    def equalizzatore_audio(self):
        originali = list(self.sessione.config.get("eq_bande", [0] * 10))
        if len(originali) != 10:
            originali = [0] * 10
        finestra = QDialog(self)
        finestra.setWindowTitle(_("Audio equalizer"))
        finestra.setModal(True)
        finestra.setStyleSheet("QDialog{background:#1c1b22;color:#e0e0e0}")
        layout = QVBoxLayout(finestra)
        col = QHBoxLayout()
        layout.addLayout(col)
        slider = []
        for frequenza, valore in zip(("31", "62", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"), originali):
            cella = QVBoxLayout()
            cella.addWidget(QLabel(frequenza))
            s = QSlider(Qt.Vertical)
            s.setRange(-12, 12)
            s.setValue(int(valore))
            s.valueChanged.connect(lambda _v: self._eq_anteprima(slider))
            slider.append(s)
            cella.addWidget(s)
            col.addLayout(cella)
        comandi = QHBoxLayout()
        flat = QPushButton(_("Flat"))
        cancel = QPushButton(_("Cancel"))
        ok = QPushButton(_("OK"))
        comandi.addWidget(flat)
        comandi.addStretch(1)
        comandi.addWidget(cancel)
        comandi.addWidget(ok)
        layout.addLayout(comandi)
        flat.clicked.connect(lambda: [s.setValue(0) for s in slider])
        cancel.clicked.connect(finestra.reject)
        ok.clicked.connect(finestra.accept)
        finestra.resize(620, 290)
        risultato = finestra.exec()
        if risultato:
            self.sessione.config["eq_bande"] = [s.value() for s in slider]
            scrivi_config(self.sessione.config)
        else:
            self.sessione.config["eq_bande"] = originali
        self.applica_filtri_audio()

    def _eq_anteprima(self, slider):
        self.sessione.config["eq_bande"] = [s.value() for s in slider]
        self.applica_filtri_audio()

    def _aggiorna_mpris(self):
        self.mpv = self._attivo()
        if not self._mpris:
            return
        player = self.mpv
        titolo, artista, album, arte = self.nome_in_onda, "", "", ""
        durata = player.duration if player else 0
        if self.file_in_onda and os.path.isabs(self.file_in_onda):
            estensione = os.path.splitext(self.file_in_onda)[1][1:].lower()
            if estensione in AUDIO:
                tag_titolo, artista, album, _anno = tag_di(self.file_in_onda, self.tag_cache)
                if not (tag_titolo or artista or album):
                    tag_titolo, artista, album, _anno = dal_percorso(
                        self.file_in_onda, self.sessione.config.get("cartelle", []))
                titolo = tag_titolo or titolo
            else:
                titolo = titolo_anno(self.file_in_onda)[0] or titolo
            copertina = copertina_url(self.file_in_onda)
            if os.path.isfile(copertina):
                arte = copertina
            if not arte and artista:
                foto = self.artwork_artista.percorso_foto(artista)
                if os.path.isfile(foto):
                    arte = foto
            if not arte:
                poster = poster_film(self.file_in_onda)
                if poster and os.path.isfile(poster):
                    arte = poster
        elif self.file_in_onda:
            programma = self._programma_corrente()
            artista = programma[2] if programma else ""
            logo = LOGHI.get(self.file_in_onda)
            if logo:
                percorso_logo = os.path.join(
                    CACHE_LOGHI, hashlib.md5(logo.encode()).hexdigest())
                if os.path.isfile(percorso_logo) and os.path.getsize(percorso_logo):
                    arte = percorso_logo
        if not arte:
            icona = os.path.join(QUI, "icon.png")
            arte = icona if os.path.isfile(icona) else ""
        try:
            pausa = player.leggi("pause") == "yes" if player else True
            self._mpris.aggiorna({
                "titolo": titolo,
                "artista": artista,
                "album": album,
                "arte": arte,
                "stato": "Stopped" if not self.file_in_onda else ("Paused" if pausa else "Playing"),
                "volume": self.volume.value() / 100.0,
                "durata": durata,
                "shuffle": self.shuffle_attivo,
                "giro_ripeti": {"uno": "Track", "tutti": "Playlist"}.get(self.ripeti, "None"),
                "giro": self._giro_traccia,
            })
        except Exception:
            pass

    def chiudi(self):
        self.close()

    def mpris_alza(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def mpris_comando(self, comando):
        player = self._attivo()
        if not player:
            return
        if comando == "playpause":
            self.pausa()
        elif comando == "play":
            player.pausa(False)
        elif comando == "pause":
            player.pausa(True)
        self._aggiorna_mpris()

    def mpris_posizione(self, secondi):
        player = self._attivo()
        if player:
            player.seek(secondi)
        self._aggiorna_mpris()

    def avanza(self, secondi):
        player = self._attivo()
        if player:
            player.seek(secondi, assoluto=False)

    def _evento_player(self, player, evento):
        if player not in (self.player, self.player2) or not isinstance(evento, dict):
            return
        if player is not self._attivo():
            return
        if evento.get("id") == MpvVideo.MPV_EVENT_FILE_LOADED:
            self._aggiorna_visibilita_capitoli()
            percorso = self._ripresa_traccia
            if percorso and percorso == self.file_in_onda:
                self._ripresa_traccia = None
                try:
                    posizione = float(self.sessione.config.get("posizioni", {}).get(percorso, 0.0))
                    durata = float(player.leggi("duration") or 0)
                    if posizione >= 10 and durata > posizione + 20:
                        player.seek(posizione)
                except Exception:
                    pass
            return
        if evento.get("id") != MpvVideo.MPV_EVENT_END_FILE:
            return
        motivo = evento.get("motivo")
        errore = evento.get("errore_file") or evento.get("errore")
        if motivo == 4 or (isinstance(errore, int) and errore < 0):
            self.canale_morto()
        elif motivo == 0 and self.file_in_onda:
            if not self._eof_gestito:
                self._eof_gestito = True
                if os.path.isabs(self.file_in_onda):
                    self.prossimo_file()
                elif self.ripeti == "tutti":
                    self.salta(1)

    def dvd_bloccato(self):
        if not (self.file_in_onda or "").startswith("dvd://"):
            return
        self.attesa_da = 0.0
        player = self._attivo()
        if player:
            try:
                player.ferma()
            except Exception:
                pass
        self._sfondo_forzato = True
        self._aggiorna_sfondo()
        self._messaggio_temporaneo(_("This DVD can't be played"))

    def canale_morto(self):
        if (self.file_in_onda or "").startswith("dvd://"):
            self.dvd_bloccato()
            return
        self.attesa_da = 0.0
        self.salti += 1
        limite = min(10, max(1, len(self._canali_visibili)))
        if self.salti >= limite:
            self.salti = 0
            self._sfondo_forzato = True
            self._aggiorna_sfondo()
            self._messaggio_temporaneo(_("%s is not responding, nor are the next ones") % self.nome_in_onda)
            return
        self._sfondo_forzato = True
        self._aggiorna_sfondo()
        self._messaggio_temporaneo(_("%s is not responding: skipping to the next") % self.nome_in_onda)
        QTimer.singleShot(600, lambda: self.salta(1))

    def prossimo_file(self):
        percorso = self.file_in_onda
        indice = next((i for i, voce in enumerate(self._canali_visibili)
                       if voce[1] == percorso), -1)
        if indice < 0:
            return
        if self.ripeti == "uno":
            self.apri(percorso, nome=self.nome_in_onda, ide=self.ide_in_onda)
        elif indice + 1 < len(self._canali_visibili):
            voce = self._canali_visibili[indice + 1]
            self._indice_canale = indice + 1
            self.apri(voce[1], nome=voce[0], ide=voce[2])
        elif self.ripeti == "tutti":
            voce = self._canali_visibili[0]
            self._indice_canale = 0
            self.apri(voce[1], nome=voce[0], ide=voce[2])

    @staticmethod
    def _tempo_testo(secondi):
        secondi = max(0, int(secondi))
        ore, resto = divmod(secondi, 3600)
        minuti, secondi = divmod(resto, 60)
        return "%02d:%02d:%02d" % (ore, minuti, secondi) if ore else "%02d:%02d" % (minuti, secondi)

    def loop_ab_imposta_a(self):
        player = self._attivo()
        if not self.file_in_onda or player is None:
            self._messaggio_temporaneo(_("A-B loop works with media files"))
            return
        try:
            posizione = float(player.leggi("time-pos"))
            self.loop_ab_a = posizione
            self.loop_ab_b = None
            self.loop_ab_file = self.file_in_onda
            self.loop_ab_in_corso = False
            self._messaggio_temporaneo(_("A point set: %s") % self._tempo_testo(posizione))
        except (TypeError, ValueError):
            self._messaggio_temporaneo(_("cannot set A-B loop point"))

    def loop_ab_imposta_b(self):
        player = self._attivo()
        if not self.file_in_onda or self.loop_ab_file != self.file_in_onda or self.loop_ab_a is None or player is None:
            self._messaggio_temporaneo(_("Set A before setting B"))
            return
        try:
            posizione = float(player.leggi("time-pos"))
            if posizione <= self.loop_ab_a:
                self._messaggio_temporaneo(_("B point must be after A"))
                return
            self.loop_ab_b = posizione
            self.loop_ab_in_corso = True
            self._messaggio_temporaneo(_("A-B loop active: %s - %s") % (
                self._tempo_testo(self.loop_ab_a), self._tempo_testo(self.loop_ab_b)))
        except (TypeError, ValueError):
            self._messaggio_temporaneo(_("cannot set A-B loop point"))

    def loop_ab_azzera(self):
        self.loop_ab_a = None
        self.loop_ab_b = None
        self.loop_ab_file = None
        self.loop_ab_in_corso = False
        self._messaggio_temporaneo(_("A-B loop cleared"))

    def metti_velocita(self, valore):
        try:
            valore = float(valore)
            if valore not in (0.5, 0.75, 1, 1.25, 1.5, 2):
                return
            self.velocita = valore
            self._imposta("speed", valore)
            if valore == 1:
                self.speed_button.hide()
            else:
                self.speed_button.setText("x%g" % valore)
                self.speed_button.show()
            self._messaggio_temporaneo(_("speed x%g") % valore)
        except Exception:
            pass

    def gira_velocita(self):
        valori = (1, 1.25, 1.5, 2, 0.5, 0.75)
        indice = valori.index(self.velocita) if self.velocita in valori else 0
        self.metti_velocita(valori[(indice + 1) % len(valori)])

    def imposta_timer_spegnimento(self, minuti):
        self.annulla_timer_spegnimento(silenzioso=True)
        try:
            minuti = int(minuti)
            self._timer_spegnimento.start(minuti * 60000)
            self.timer_fine = time.time() + minuti * 60
            self._messaggio_temporaneo(_("sleep timer set: %d min") % minuti)
        except Exception:
            self.timer_fine = None
            self._messaggio_temporaneo(_("cannot set sleep timer"))

    def annulla_timer_spegnimento(self, silenzioso=False):
        self._timer_spegnimento.stop()
        self.timer_fine = None
        if not silenzioso:
            self._messaggio_temporaneo(_("sleep timer cancelled"))

    def scade_timer_spegnimento(self):
        self.timer_fine = None
        self.ferma()
        self._messaggio_temporaneo(_("sleep timer expired"))

    def salta(self, direzione):
        if not self._canali_visibili:
            return
        if self._indice_canale < 0:
            self._indice_canale = 0
        else:
            self._indice_canale = (self._indice_canale + direzione) % len(self._canali_visibili)
        voce = self._canali_visibili[self._indice_canale]
        self.apri(voce[1], nome=voce[0], ide=voce[2])

    def mpris_shuffle(self, attivo):
        attivo = bool(attivo)
        if attivo == self.shuffle_attivo:
            return
        self.shuffle_attivo = attivo
        self._ordine_shuffle = None
        if attivo and self._canali_visibili and all(os.path.isabs(v[1]) for v in self._canali_visibili):
            self._ordine_vero = list(self._canali_visibili)
            mischiati = list(self._canali_visibili)
            random.shuffle(mischiati)
            in_onda = [v for v in mischiati if v[1] == self.file_in_onda]
            mischiati = in_onda + [v for v in mischiati if v[1] != self.file_in_onda]
            self._ordine_shuffle = [v[1] for v in mischiati]
        elif not attivo:
            self._ordine_vero = None
        if hasattr(self, "shuffle_button"):
            self.shuffle_button.setChecked(self.shuffle_attivo)
            self.shuffle_button.setToolTip(_("Shuffle on") if self.shuffle_attivo else _("Shuffle"))
        if hasattr(self, "azione_shuffle"):
            self.azione_shuffle.setChecked(self.shuffle_attivo)
        self.sessione.config["shuffle"] = self.shuffle_attivo
        scrivi_config(self.sessione.config)
        if hasattr(self, "elenco"):
            self._riempi_elenco()
        self._aggiorna_mpris()

    def _aggiorna_azioni_ripeti(self):
        for chiave, azione in getattr(self, "azioni_ripeti", {}).items():
            azione.setChecked(chiave == self.ripeti)

    def _aggiorna_icone_ripeti(self):
        pulsante = self._pulsanti.get("repeat")
        if pulsante is None:
            return
        nome = "repeat_one" if self.ripeti == "uno" else "repeat"
        percorso = os.path.join(QUI, "icone", nome + ".png")
        if os.path.isfile(percorso):
            pulsante.setIcon(QIcon(percorso))
        etichetta = {"": _("Repeat off"), "uno": _("Repeat file"),
                     "tutti": _("Repeat playlist")}.get(self.ripeti, _("Repeat off"))
        pulsante.setToolTip(etichetta)

    def metti_ripeti(self, modalita):
        self.ripeti = modalita or ""
        self.sessione.config["ripeti"] = self.ripeti
        scrivi_config(self.sessione.config)
        player = self._attivo()
        if player:
            player.imposta("loop-file", "inf" if self.ripeti == "uno" else "no")
            player.imposta("loop-playlist", "inf" if self.ripeti == "tutti" else "no")
        self._aggiorna_azioni_ripeti()
        self._aggiorna_icone_ripeti()
        self._aggiorna_mpris()


    def _imposta_categoria_attiva(self, percorso):
        categoria = None
        if percorso and not os.path.isabs(percorso):
            categoria = next((voce[3] for voce in self.sessione.canali
                              if len(voce) > 3 and voce[1] == percorso), None)
        self._categoria_attiva = str(categoria).strip() if categoria else None
        self.et_categoria.setText(self._categoria_attiva or "")
        self.et_categoria.setVisible(bool(self._categoria_attiva))

    def aggiorna_info_canale(self):
        if self.registrando:
            self._mostra_rec()
            return
        if not self.file_in_onda:
            self.et_ora_programma.hide()
            self.et_prossimo.hide()
            self.et_ora_prossimo.hide()
            return
        programma = self._programma_corrente()
        prossimo = self._programma_successivo()
        if programma:
            self.riga_stato.setText("%s  ·  %s" % (self.nome_in_onda, programma[2]))
            self.et_ora_programma.setText(
                "%s–%s" % (time.strftime("%H:%M", time.localtime(programma[0])),
                           time.strftime("%H:%M", time.localtime(programma[1]))))
            self.et_ora_programma.show()
        else:
            self.riga_stato.setText(self.nome_in_onda)
            self.et_ora_programma.hide()
        if prossimo:
            self.et_prossimo.setText(_("Next: %s") % prossimo[2])
            self.et_ora_prossimo.setText(time.strftime("%H:%M", time.localtime(prossimo[0])))
            self.et_prossimo.show()
            self.et_ora_prossimo.show()
        else:
            self.et_prossimo.hide()
            self.et_ora_prossimo.hide()
        self.elenco.viewport().update()

    def _programmi_canale(self):
        if not self.ide_in_onda and not self.nome_in_onda:
            return []
        chiave = self.ide_in_onda if self.ide_in_onda in self.sessione.epg else self.sessione.epg_nomi.get(
            __import__("core.epg", fromlist=["nome_piatto"]).nome_piatto(self.nome_in_onda))
        return self.sessione.epg.get(chiave, []) if chiave else []

    def _programma_corrente(self):
        adesso = time.time()
        return next((programma for programma in self._programmi_canale()
                     if programma[0] <= adesso < programma[1]), None)

    def _programma_successivo(self):
        adesso = time.time()
        return next((programma for programma in self._programmi_canale()
                     if programma[0] > adesso), None)

    def registra(self):
        if self.registrando:
            self.ferma_registrazione()
            return
        f = self.file_in_onda or ""
        if f.startswith("dvd://"):
            if dvd_cifrato(f[len("dvd://"):]):
                self.riga_stato.setText(_("This DVD is protected and can't be recorded"))
                return
        elif f and not re.match(r"https?://", f, re.I):
            return
        if not f or not self.nome_in_onda:
            return
        self.avvia_registrazione(self.nome_in_onda, 0.0)

    def avvia_registrazione(self, nome, fine):
        player = self._attivo()
        if not player:
            return
        try:
            os.makedirs(REGISTRAZIONI, exist_ok=True)
            programma = self._programma_corrente()
            titolo = (programma[2] if programma and programma[2] else "") or nome
            pulisci = lambda t: re.sub(r'[\\/:*?"<>|]+', "", t).strip() or "xvb"
            cartella = os.path.join(REGISTRAZIONI, pulisci(nome))
            os.makedirs(cartella, exist_ok=True)
            video = player.leggi("vid")
            estensione = "mkv" if video not in (None, "no", "0") else "mka"
            destinazione = os.path.join(
                cartella, "%s - %s.%s" % (
                    pulisci(titolo), time.strftime("%Y-%m-%d %H-%M"), estensione))
            player.imposta("stream-record", destinazione)
        except Exception as errore:
            self.riga_stato.setText("Cannot record: " + str(errore))
            return
        self.registrando = destinazione
        self._player_rec = player
        self._imposta_pulsante_rec(True)
        self.fine_rec = fine
        self.inizio_rec = time.time()
        self._mostra_rec()

    def ferma_registrazione(self):
        player = self._player_rec or self._attivo()
        if player:
            try:
                player.imposta("stream-record", "")
            except Exception:
                pass
        destinazione = self.registrando
        self.registrando = ""
        self._player_rec = None
        self._imposta_pulsante_rec(False)
        self.fine_rec = 0.0
        if destinazione:
            self.riga_stato.setText("Saved " + os.path.basename(destinazione))
            self._riempi_liste()

    def _imposta_pulsante_rec(self, attiva):
        pulsante = self._pulsanti.get("rec")
        if pulsante is None:
            return
        nome = "rec_stop" if attiva else "rec"
        percorso = os.path.join(QUI, "icone", nome + ".png")
        if os.path.isfile(percorso):
            pulsante.setIcon(QIcon(percorso))
        pulsante.setToolTip(_("Stop") if attiva else _("Record"))

    def _mostra_rec(self):
        if not self.registrando:
            return
        durata = int(time.time() - self.inizio_rec)
        ore, resto = divmod(durata, 3600)
        cronometro = ("%d:%02d:%02d" % (ore, resto // 60, resto % 60)
                      if ore else "%02d:%02d" % (resto // 60, resto % 60))
        stato = "REC " + cronometro
        if self.fine_rec:
            stato += "  until " + time.strftime("%H:%M", time.localtime(self.fine_rec))
        self.riga_stato.setText(stato)

    @staticmethod
    def ora_di(testo, dopo=None):
        h, m = (int(x) for x in testo.strip().split(":"))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError(testo)
        adesso = time.localtime()
        t = time.mktime((adesso.tm_year, adesso.tm_mon, adesso.tm_mday,
                         h, m, 0, 0, 0, -1))
        base = dopo if dopo is not None else time.time()
        while t <= base:
            t += 86400
        return t

    def pianifica(self):
        if not self.file_in_onda or not self.nome_in_onda:
            self.riga_stato.setText("Open the channel to record first")
            return
        inizio = self._chiedi_testo(_("Schedule"), _("Start (HH:MM):"),
                                     time.strftime("%H:%M"))
        if not inizio:
            return
        fine = self._chiedi_testo(_("Schedule"), _("End (HH:MM):"))
        if not fine:
            return
        try:
            t0 = self.ora_di(inizio)
            t1 = self.ora_di(fine, dopo=t0)
        except (ValueError, TypeError):
            self.riga_stato.setText("Time must be HH:MM")
            return
        self.piano = (self.nome_in_onda, self.file_in_onda, self.ide_in_onda, t0, t1)
        self.riga_stato.setText("Scheduled %s: %s–%s" % (
            self.nome_in_onda, time.strftime("%H:%M", time.localtime(t0)),
            time.strftime("%H:%M", time.localtime(t1))))

    def annulla_piano(self):
        self.piano = None
        self.riga_stato.setText("Schedule cancelled")

    def controlla_registrazione(self):
        adesso = time.time()
        if self.piano and adesso >= self.piano[3]:
            nome, url, ide, _inizio, fine = self.piano
            self.piano = None
            if adesso < fine:
                if self.file_in_onda != url:
                    self.apri(url, nome=nome, ide=ide)
                    QTimer.singleShot(5000, lambda: self.avvia_registrazione(nome, fine))
                else:
                    self.avvia_registrazione(nome, fine)
        if self.registrando and self.fine_rec and adesso >= self.fine_rec:
            self.ferma_registrazione()
        elif self.registrando:
            self._mostra_rec()

    def apri_registrazioni(self):
        os.makedirs(REGISTRAZIONI, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(REGISTRAZIONI))


    def recenti(self):
        return [p for p in self.sessione.config.get("recenti", []) if os.path.isfile(p)][:8]

    def _aggiorna_recenti(self):
        if not hasattr(self, "menu_recenti"):
            return
        self.menu_recenti.clear()
        for percorso in self.recenti():
            self.menu_recenti.addAction(
                self._azione(os.path.basename(percorso), lambda _=False, p=percorso: self.apri(p)))
        self.menu_recenti.setEnabled(bool(self.recenti()))

    def pulisci_recenti(self):
        self.sessione.config["recenti"] = []
        scrivi_config(self.sessione.config)
        self._aggiorna_recenti()


    def _importa_percorsi(self, percorsi):
        importati = self.sessione.config.setdefault("importati", [])
        aggiunti = 0
        for percorso in percorsi:
            if not os.path.isfile(percorso) or percorso in importati:
                continue
            importati.append(percorso)
            estensione = os.path.splitext(percorso)[1][1:].lower()
            if estensione in AUDIO:
                titolo, artista, album, anno = tag_di(percorso, self.tag_cache)
                nome = titolo or os.path.splitext(os.path.basename(percorso))[0]
                self.sottotitoli[percorso] = " · ".join(x for x in (artista, album, anno) if x)
                categoria = "Music"
            else:
                nome, anno = titolo_anno(percorso)
                nome = nome or os.path.splitext(os.path.basename(percorso))[0]
                self.sottotitoli[percorso] = anno or ""
                categoria = "Video"
            self.sessione.canali.append((nome, percorso, None, categoria, "__importati__"))
            aggiunti += 1
        scrivi_config(self.sessione.config)
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self._riempi_liste()
        return aggiunti

    def dragEnterEvent(self, evento):
        if evento.mimeData().hasUrls():
            evento.acceptProposedAction()
        else:
            evento.ignore()

    def dropEvent(self, evento):
        percorsi = []
        for url in evento.mimeData().urls():
            percorso = url.toLocalFile()
            if percorso and os.path.exists(percorso):
                percorsi.append(percorso)
        if percorsi:
            self.apri_da_fuori(percorsi)
            evento.acceptProposedAction()
        else:
            evento.ignore()

    def apri_da_fuori(self, percorsi):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        file_media = []
        cartelle = []
        liste = []
        for percorso in percorsi:
            percorso = os.path.abspath(percorso)
            if os.path.isdir(percorso):
                if percorso not in cartelle:
                    cartelle.append(percorso)
            elif os.path.isfile(percorso) and e_media(percorso):
                if percorso not in file_media:
                    file_media.append(percorso)
            elif os.path.isfile(percorso) and e_una_lista(percorso):
                if percorso not in liste:
                    liste.append(percorso)
        cfg = self.sessione.config
        archivio = cfg.setdefault("liste", [])
        archivio.extend(p for p in liste if p not in archivio)
        cartelle_cfg = cfg.setdefault("cartelle", [])
        nuove_cartelle = [p for p in cartelle if p not in cartelle_cfg]
        cartelle_cfg.extend(nuove_cartelle)
        scrivi_config(cfg)
        if liste:
            self.ricarica_liste(scegli=liste[0], forza=False)
        if not nuove_cartelle:
            self._completa_apri_da_fuori(file_media, nuove_cartelle, {})
            return
        self.riga_stato.setText(_("Loading media folders..."))
        worker = _ScansionaCartelle(nuove_cartelle, self.tag_cache)
        worker.completato.connect(
            lambda risultati, errore, fm=file_media, nc=nuove_cartelle:
                self._cartelle_drop_scansionate(fm, nc, risultati, errore))
        worker.finished.connect(lambda w=worker: self._rimuovi_worker_scansione(w))
        self.__dict__.setdefault("_scan_workers", []).append(worker)
        worker.start()

    def _cartelle_drop_scansionate(self, file_media, cartelle, risultati, errore):
        if errore:
            self.riga_stato.setText(_("Unable to scan media folders: %s") % errore)
        self._completa_apri_da_fuori(file_media, cartelle, risultati)

    def _completa_apri_da_fuori(self, file_media, nuove_cartelle, risultati):
        for cartella in nuove_cartelle:
            nuovi = self._media_locale(cartella, risultati.get(cartella, []))
            if not nuovi:
                continue
            self.sessione.canali.extend(nuovi)
            self.sessione.liste.append({
                "percorso": cartella, "nome": os.path.basename(cartella),
                "canali": [(n, p, ide) for n, p, ide, _cat, _lista in nuovi],
                "categorie": {p: cat for _n, p, _ide, cat, _lista in nuovi},
            })
        non_importati = [p for p in file_media
                         if not any(voce[1] == p for voce in self.sessione.canali)]
        if non_importati:
            self._importa_percorsi(non_importati)
        if file_media:
            prima = file_media[0]
            voce = next((v for v in self.sessione.canali if v[1] == prima), None)
            if voce is not None:
                if voce[4] == "__importati__":
                    self._percorso_attivo, self._categoria_attiva = "__importati__", None
                else:
                    self._percorso_attivo, self._categoria_attiva = voce[4], None
        elif nuove_cartelle:
            self._percorso_attivo, self._categoria_attiva = nuove_cartelle[0], None
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self._riempi_liste()
        self._riempi_elenco()
        if file_media:
            prima = file_media[0]
            voce = next((v for v in self.sessione.canali if v[1] == prima), None)
            self.apri(prima, nome=voce[0] if voce else os.path.basename(prima),
                      ide=voce[2] if voce else None)

    def importa_file(self):
        percorsi, _ = QFileDialog.getOpenFileNames(
            self, _("Import media files"), self.sessione.config.get("ultima_cartella", ""))
        if not percorsi:
            return
        self._importa_percorsi(percorsi)
        self._percorso_attivo, self._categoria_attiva = "__importati__", None
        self._riempi_elenco()
        self.riga_stato.setText(_("%d media files imported") % len(percorsi))

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(
            self, _("Open file"), self.sessione.config.get("ultima_cartella", ""))
        if percorso:
            self.sessione.config["ultima_cartella"] = os.path.dirname(percorso)
            self._importa_percorsi([percorso])
            self._percorso_attivo, self._categoria_attiva = "__importati__", None
            self._riempi_elenco()
            voce = next((v for v in self.sessione.canali if v[1] == percorso), None)
            self.apri(percorso, nome=voce[0] if voce else os.path.basename(percorso))

    def _via_url_temporanei(self):
        config = self.sessione.config
        for url in config.get("url_aperti", []):
            config.get("nomi_url", {}).pop(url, None)
            try:
                os.remove(copertina_url(url))
            except OSError:
                pass
        config["url_aperti"] = []

    def url_di(self, categoria=None):
        if categoria is None:
            return self.sessione.config.get("url_aperti", [])
        return self.sessione.config.get("url_salvati", {}).get(categoria, [])

    def nome_di_url(self, url):
        return self.sessione.config.get("nomi_url", {}).get(url) or titolo_url(url)

    def metti_url(self, categoria, url):
        salvati = self.sessione.config.setdefault("url_salvati", {})
        for chiave, _nome in CATEGORIE_URL:
            salvati[chiave] = [u for u in salvati.get(chiave, []) if u != url]
        self.sessione.config["url_aperti"] = [
            u for u in self.sessione.config.get("url_aperti", []) if u != url]
        if categoria is None:
            self.sessione.config["url_aperti"] = ([url] + self.sessione.config["url_aperti"])[:20]
        else:
            salvati[categoria] = [url] + salvati.get(categoria, [])


    def rinomina_url(self, url):
        nome = self._chiedi_testo(_("Rename..."), _("Name:"), self.nome_di_url(url))
        if nome is None:
            return
        self.sessione.config.setdefault("nomi_url", {})[url] = nome.strip() or self.nome_di_url(url)
        scrivi_config(self.sessione.config)
        self._riempi_liste()
        self._riempi_elenco()

    def sposta_url(self, url, categoria):
        self.metti_url(categoria, url)
        self.sessione.config["ultima_categoria_url"] = categoria or ""
        scrivi_config(self.sessione.config)
        self._riempi_liste()
        self._percorso_attivo, self._categoria_attiva = "__url__", categoria
        self._riempi_elenco()

    def rimuovi_url(self, url):
        self.metti_url(None, url)
        self.sessione.config["url_aperti"] = [
            u for u in self.sessione.config.get("url_aperti", []) if u != url]
        for categoria, _nome in CATEGORIE_URL:
            self.sessione.config.setdefault("url_salvati", {}).setdefault(categoria, [])
            self.sessione.config["url_salvati"][categoria] = [
                u for u in self.sessione.config["url_salvati"][categoria] if u != url]
        self.sessione.config.get("nomi_url", {}).pop(url, None)
        scrivi_config(self.sessione.config)
        self._riempi_liste()
        self._riempi_elenco()

    def apri_url_da(self, url):
        self.apri(url, nome=self.nome_di_url(url))
        self._url_al_volo = url

    def apri_url(self):
        url = self._chiedi_testo(_("Open URL"), _("URL"))
        if not url or not url.strip():
            return
        url = url.strip()
        base = self.nome_di_url(url)
        nome = self._chiedi_testo(_("Open URL"), _("Name:"), base)
        if nome is None:
            return
        categorie = list(CATEGORIE_URL) + [(None, "Temporary")]
        etichette = [_(nome_categoria) for _chiave, nome_categoria in categorie]
        ultima = self.sessione.config.get("ultima_categoria_url", "radio")
        indice = next((i for i, (k, _n) in enumerate(categorie) if k == ultima), len(categorie) - 1)
        scelta, ok = QInputDialog.getItem(self, _("Open URL"), _("Save in:"), etichette, indice, False)
        if not ok:
            return
        categoria = categorie[etichette.index(scelta)][0]
        self.sessione.config.setdefault("nomi_url", {})[url] = nome.strip() or base
        self.sessione.config["ultima_categoria_url"] = categoria or ""
        self.metti_url(categoria, url)
        scrivi_config(self.sessione.config)
        self._riempi_liste()
        self._percorso_attivo, self._categoria_attiva = "__url__", categoria
        self._riempi_elenco()
        self.apri(url, nome=nome.strip() or base)

    def apri(self, percorso, url=None, ide=None, nome=None):
        if url is not None:
            nome = percorso
            percorso = url
        player = self._attivo()
        if player is None:
            QMessageBox.warning(self, "XVB", _("libmpv not available"))
            return
        self._eof_gestito = False
        self.salti = 0
        self._ultima_posizione = None
        self._sfondo_forzato = False
        self._giro_traccia += 1
        self.file_in_onda = percorso
        self._imposta_categoria_attiva(percorso)
        self._ripresa_traccia = percorso if os.path.isabs(percorso) else None
        if os.path.isabs(percorso) and os.path.splitext(percorso)[1][1:].lower() in AUDIO:
            self._richiedi_foto_artisti(percorso)
        self._segna_in_onda()
        self.nome_in_onda = nome or os.path.splitext(os.path.basename(percorso.rstrip("/")))[0] or percorso
        self.colora_stato(self.colore_canale(self.nome_in_onda, percorso))
        self.ide_in_onda = ide
        self.varianti = []
        self.quale = -1
        self.menu_qualita.setEnabled(False)
        self.b_qualita.hide()
        self.riga_stato.setText(self.nome_in_onda)
        self._icona_preferito()
        self._aggiorna_mpris()
        if os.path.isabs(percorso) and os.path.isfile(percorso) and not percorso.startswith(REGISTRAZIONI + os.sep):
            recenti = self.sessione.config.get("recenti", [])
            recenti = [p for p in recenti if p != percorso and os.path.isfile(p)]
            self.sessione.config["recenti"] = ([percorso] + recenti)[:12]
            scrivi_config(self.sessione.config)
            self._aggiorna_recenti()
        try:
            player.imposta("audio-files", "[]")
            if percorso.startswith("http://") or percorso.startswith("https://"):
                ritardi = self.sessione.config.get("ritardo", {})
                try:
                    player.imposta("audio-delay", float(ritardi.get(percorso, 0.0)))
                except Exception:
                    pass
                try:
                    player.imposta(
                        "stream-lavf-o",
                        "" if "jmp2.uk" in percorso else
                        "reconnect=1,reconnect_streamed=1,reconnect_on_network_error=1,reconnect_delay_max=10")
                except Exception:
                    pass
                self.applica_chiave(percorso, player)
                self._stream_player = player
                self.riga_stato.setText(_("looking for %s qualities...") % self.nome_in_onda)
                worker = _RisolviStream(percorso)
                worker.completato.connect(
                    lambda u, elenco, errore, p=player: self._stream_pronto(p, u, elenco, errore))
                worker.finished.connect(lambda w=worker: self._rimuovi_worker_stream(w))
                self._stream_workers.append(worker)
                worker.start()
            else:
                try:
                    player.imposta("audio-delay", float(
                        self.sessione.config.get("ritardo", {}).get(percorso, 0.0)))
                except Exception:
                    pass
                player.apri(percorso)
                self.play_button.setIcon(QIcon(os.path.join(QUI, "icone", "pausa.png")))
                self.play_button.setToolTip(_("Pause"))
            self._aggiorna_mpris()
        except Exception as errore:
            QMessageBox.critical(self, "XVB", str(errore))

    def _rimuovi_worker_stream(self, worker):
        if worker in self._stream_workers:
            self._stream_workers.remove(worker)

    def indirizzo_chiave(self, url):
        if chiave_clearkey(CHIAVI.get(url)) and url.split("?")[0].lower().endswith(".mpd"):
            try:
                return "http://127.0.0.1:%d/m.mpd?u=%s" % (
                    server_mpd().server_address[1], quote(url, safe=""))
            except Exception:
                pass
        return url

    def applica_chiave(self, url, player=None):
        player = player or self._attivo()
        protocolli = "file,http,https,tcp,tls,crypto,data,httpproxy,udp,rtp,rtmp,rtmps,srt"
        opzioni = "protocol_whitelist=%%%d%%%s" % (len(protocolli), protocolli)
        chiave = chiave_clearkey(CHIAVI.get(url))
        if chiave:
            opzioni += ",cenc_decryption_key=" + chiave
        if player:
            try:
                player.imposta("demuxer-lavf-o", opzioni)
            except Exception:
                pass

    def _stream_pronto(self, player, url, elenco, errore=""):
        if self.file_in_onda != url:
            return
        self.varianti = elenco or []
        self.menu_qualita.setEnabled(len(self.varianti) > 1)
        self.b_qualita.setVisible(len(self.varianti) > 1)
        if errore:
            self.riga_stato.setText(_("Stream resolution failed: %s") % errore)
        if self.varianti:
            salvata = self.sessione.config.get("qualita", {}).get(url, len(self.varianti) - 1)
            self.quale = salvata if isinstance(salvata, int) and -1 <= salvata < len(self.varianti) else len(self.varianti) - 1
            if self.quale >= 0:
                self.suona(self.quale, player)
            else:
                player.apri(self.indirizzo_chiave(url))
        else:
            self.quale = -1
            player.apri(self.indirizzo_chiave(url))
        self.play_button.setIcon(QIcon(os.path.join(QUI, "icone", "pausa.png")))
        self.play_button.setToolTip(_("Pause"))
        self.riga_stato.setText(self.nome_in_onda)
        self._aggiorna_mpris()

    def suona(self, indice, player=None):
        player = player or self._stream_player or self._attivo()
        if not player or not self.varianti:
            return
        _banda, video, _audio, _altezza, master = self.varianti[indice]
        try:
            player.imposta("audio-files", "[]")
        except Exception:
            pass
        try:
            os.makedirs(CACHE_VARIANTE, exist_ok=True)
            nome = "variante2.m3u8" if self.split and player is self.player2 else "variante.m3u8"
            destinazione = os.path.join(CACHE_VARIANTE, nome)
            with open(destinazione, "w", encoding="utf-8") as stream:
                stream.write(master)
            player.apri(destinazione)
        except Exception:
            player.apri(video)
        self.quale = indice
        self.sessione.config.setdefault("qualita", {})[self.file_in_onda] = indice
        scrivi_config(self.sessione.config)

    def scegli_qualita(self, indice):
        if indice == -1:
            self.quale = -1
            if self._stream_player:
                self._stream_player.apri(self.indirizzo_chiave(self.file_in_onda))
        elif indice != self.quale and self.varianti:
            self.suona(indice)
        self._aggiorna_mpris()

    def _apri_menu_qualita(self):
        punto = self.b_qualita.mapToGlobal(self.b_qualita.rect().bottomLeft())
        self.menu_qualita.popup(punto)

    def _riempi_menu_qualita(self):
        self.menu_qualita.clear()
        if not self.varianti:
            azione = self.menu_qualita.addAction(_("Automatic"))
            azione.setEnabled(False)
            return
        self.menu_qualita.addAction(self._azione(
            ("✓  " if self.quale == -1 else "") + _("Automatic"),
            lambda: self.scegli_qualita(-1)))
        for i, variante in enumerate(self.varianti):
            banda, _video, _audio, altezza, _master = variante
            testo = "%dp · %d kb/s" % (altezza, banda // 1000) if altezza else "%d kb/s" % (banda // 1000)
            if self.quale == i:
                testo = "✓  " + testo
            self.menu_qualita.addAction(
                self._azione(testo, lambda _=False, n=i: self.scegli_qualita(n)))

    def pausa(self):
        fermato = getattr(self, "fermato", None)
        if fermato:
            self.fermato = None
            _tipo, nome, percorso, ide = fermato
            self.apri(percorso, nome=nome, ide=ide)
            return
        player = self._attivo()
        if player:
            player.pausa()
            fermo = player.leggi("pause") == "yes"
            percorso = os.path.join(QUI, "icone", "play" if fermo else "pausa")
            self.play_button.setIcon(QIcon(percorso + ".png"))
            self.play_button.setToolTip(_("Resume") if fermo else _("Pause"))
            self._aggiorna_mpris()

    def ferma(self):
        self.annulla_timer_spegnimento(silenzioso=True)
        if self.registrando:
            self.ferma_registrazione()
        player = self._attivo()
        if player:
            if self.file_in_onda:
                self.fermato = ("file", self.nome_in_onda, self.file_in_onda, self.ide_in_onda)
            player.ferma()
            self.file_in_onda = None
            self._imposta_categoria_attiva(None)
            self._segna_in_onda()
            self.nome_in_onda = ""
            self.play_button.setIcon(QIcon(os.path.join(QUI, "icone", "play.png")))
            self.play_button.setToolTip(_("Resume"))
            self.riga_stato.setText("XVB")
            self.colora_stato(None)
            self._icona_preferito()
            self._aggiorna_sfondo()
            self._aggiorna_mpris()

    def dispositivi_uscita_audio(self):
        player = self._attivo()
        if player is None:
            return []
        try:
            elenco = player.leggi_nodo("audio-device-list") or []
        except Exception:
            elenco = []
        risultati = []
        for voce in elenco:
            if not isinstance(voce, dict):
                continue
            nome = voce.get("name")
            descrizione = voce.get("description") or nome
            if nome and str(nome) != "auto":
                risultati.append((str(nome), str(descrizione)))
        return risultati

    def applica_uscita_audio(self, nome=None, silenzioso=False):
        player = self._attivo()
        if player is None:
            return False
        if nome is None:
            nome = self.sessione.config.get("audio_device", "auto")
        nome = str(nome or "auto")
        try:
            player.imposta("audio-device", nome)
            attuale = player.leggi("audio-device")
            if nome != "auto" and attuale and str(attuale) != nome:
                raise RuntimeError(str(attuale))
            return True
        except Exception as errore:
            if nome != "auto":
                try:
                    player.imposta("audio-device", "auto")
                except Exception:
                    pass
            if not silenzioso:
                self._messaggio_temporaneo(_("cannot set audio output: %s") % errore)
            return False

    def scegli_uscita_audio(self):
        dispositivi = [("auto", _("Auto (system default)"))]
        dispositivi.extend(self.dispositivi_uscita_audio())
        finestra = Finestrella(
            self, _("Audio output device"),
            lambda dialogo: self._corpo_uscita_audio(dialogo, dispositivi),
            ok=_("Apply"), annulla=_("Cancel"), domanda=True, larga=520)
        if finestra.exec() != QDialog.Accepted:
            return
        indice = self.lista_uscita_audio.currentRow()
        if not 0 <= indice < len(dispositivi):
            return
        nome, descrizione = dispositivi[indice]
        if self.applica_uscita_audio(nome):
            self.sessione.config["audio_device"] = nome
            scrivi_config(self.sessione.config)
            self._messaggio_temporaneo(_("audio output: %s") % descrizione)

    def _corpo_uscita_audio(self, dialogo, dispositivi):
        dialogo.contenuto.addWidget(QLabel(_("Choose the audio output device:"), dialogo))
        self.lista_uscita_audio = QListWidget(dialogo)
        self.lista_uscita_audio.setMinimumHeight(180)
        self.lista_uscita_audio.setStyleSheet(
            "QListWidget{background:%s;color:%s;border:0}"
            "QListWidget::item:selected{background:%s;color:#17121f}" %
            (IN_ONDA, TESTO, ACCENTO))
        for nome, descrizione in dispositivi:
            item = QListWidgetItem(descrizione)
            item.setData(Qt.UserRole, nome)
            self.lista_uscita_audio.addItem(item)
        corrente = str(self.sessione.config.get("audio_device", "auto"))
        indice = next((i for i, voce in enumerate(dispositivi) if voce[0] == corrente), 0)
        self.lista_uscita_audio.setCurrentRow(indice)
        if len(dispositivi) == 1:
            dialogo.contenuto.addWidget(QLabel(_("No audio devices were reported by mpv."), dialogo))
        dialogo.contenuto.addWidget(self.lista_uscita_audio)

    def mostra_avviso(self, testo, secondi=8, chiave=None):
        self.avviso_chiave = chiave or (None, ())
        self.et_avviso.setText(testo)
        self.avviso.show()
        self._timer_avviso.stop()
        if secondi:
            self._timer_avviso.start(int(secondi * 1000))

    def chiudi_avviso(self):
        self._timer_avviso.stop()
        self.avviso.hide()
        self.avviso_chiave = (None, ())

    def _messaggio_temporaneo(self, testo):
        self.riga_stato.setText(testo)
        QTimer.singleShot(2500, self.aggiorna_info_canale)

    def ritardo_audio(self, di):
        url = self.file_in_onda
        player = self._attivo()
        if not url or player is None:
            return
        try:
            valore = round(float(player.leggi("audio-delay") or 0.0) + di, 1)
            player.imposta("audio-delay", valore)
        except Exception:
            return
        ritardi = self.sessione.config.setdefault("ritardo", {})
        if abs(valore) < 0.05:
            ritardi.pop(url, None)
        else:
            ritardi[url] = valore
        scrivi_config(self.sessione.config)
        self._messaggio_temporaneo(_("audio delay %+.1fs") % valore)

    def azzera_ritardo(self):
        player = self._attivo()
        if player is None:
            return
        try:
            valore = float(player.leggi("audio-delay") or 0.0)
        except (TypeError, ValueError):
            valore = 0.0
        if valore:
            self.ritardo_audio(-valore)

    def ritardo_sottotitoli(self, di):
        url = self.file_in_onda
        player = self._attivo()
        if not url or player is None:
            self._messaggio_temporaneo(_("nothing is playing"))
            return
        try:
            valore = round(float(player.leggi("sub-delay") or 0.0) + di, 1)
            player.imposta("sub-delay", valore)
        except Exception:
            self._messaggio_temporaneo(_("nothing is playing"))
            return
        self._messaggio_temporaneo(_("subtitle delay %+.1fs") % valore)

    def scala_sottotitoli(self, di):
        url = self.file_in_onda
        player = self._attivo()
        if not url or player is None:
            self._messaggio_temporaneo(_("nothing is playing"))
            return
        try:
            valore = min(3.0, max(0.5, round(float(player.leggi("sub-scale") or 1.0) + di, 1)))
            player.imposta("sub-scale", valore)
        except Exception:
            self._messaggio_temporaneo(_("nothing is playing"))
            return
        self._messaggio_temporaneo(_("subtitle size %d%%") % round(valore * 100))

    def azzera_sottotitoli(self):
        player = self._attivo()
        if player is None:
            return
        try:
            player.imposta("sub-delay", 0.0)
            player.imposta("sub-scale", 1.0)
        except Exception:
            pass
        self._messaggio_temporaneo(_("subtitle delay %+.1fs") % 0.0)

    def controlla_versione(self, zitto=False):
        worker = self._versione_worker
        if worker is not None and worker.isRunning():
            return
        worker = _VerificaVersione()
        self._versione_worker = worker
        worker.completato.connect(
            lambda tag, pagina, silenzioso=zitto: self._versione_pronta(tag, pagina, silenzioso))
        worker.errore.connect(
            lambda errore, silenzioso=zitto: self._versione_errore(errore, silenzioso))
        worker.start()

    def _versione_pronta(self, tag, pagina, zitto):
        if tag and piu_nuova(tag, VERSIONE):
            self.nuova, self.pagina_nuova = tag, pagina
            self.azione_download.setText(_("Download %s") % tag)
            self.azione_download.setEnabled(bool(pagina))
            self.mostra_avviso(
                _("new version %s available: Help > Download") % tag, 0,
                ("new version %s available: Help > Download", (tag,)))
        else:
            self.nuova, self.pagina_nuova = None, None
            self.azione_download.setText(_("Up to date"))
            self.azione_download.setEnabled(False)
            if not zitto:
                self._messaggio_temporaneo(_("up to date (%s)") % VERSIONE)

    def _versione_errore(self, errore, zitto):
        if not zitto:
            self._messaggio_temporaneo(_("cannot check for updates: %s") % errore)

    def apri_release(self):
        if self.pagina_nuova:
            QDesktopServices.openUrl(QUrl(self.pagina_nuova))

    def dona(self):
        if not QDesktopServices.openUrl(QUrl(DONA)):
            self._messaggio_temporaneo(_("cannot open %s") % DONA)

    def _volume(self, valore):
        player = self._attivo()
        if player:
            player.volume(float(valore) * (1.5 if self.sessione.config.get("boost") else 1.0))
        self.sessione.config["volume"] = int(valore)
        scrivi_config(self.sessione.config)
        self._icona_volume()
        self._aggiorna_mpris()

    def _seek(self):
        player = self._attivo()
        if player:
            durata = player.leggi("duration")
            if durata:
                player.seek(float(durata) * self.posizione.value() / 1000.0)


    def eventFilter(self, oggetto, evento):
        if oggetto in (getattr(self, "volume", None), getattr(self, "b_muto", None)):
            if evento.type() == evento.Type.Enter:
                self.apri_volume()
            elif evento.type() == evento.Type.Leave:
                self.chiudi_volume_tra_poco()
        if evento.type() == evento.Type.MouseButtonPress and oggetto in (self.avviso, self.et_avviso):
            self.chiudi_avviso()
        if evento.type() == evento.Type.Resize and oggetto is self.video:
            self._posiziona_overlay()
        elif evento.type() == evento.Type.Resize and oggetto is self.barra:
            self.posizione.setGeometry(0, 30, self.barra.width(), 10)
        if evento.type() in (evento.Type.MouseMove, evento.Type.MouseButtonPress):
            if self._overlay_attivo and (oggetto is self.player or oggetto is self.video
                                         or oggetto is self.barra
                                         or self.barra.isAncestorOf(oggetto)):
                self._mostra_overlay()
            if evento.type() == evento.Type.MouseButtonPress:
                if oggetto is self.player:
                    self.schermo_attivo = 0
                elif oggetto is self.player2:
                    self.schermo_attivo = 1
        return super().eventFilter(oggetto, evento)

    def split_si_no(self):
        if self.split:
            self.chiudi_split()
        else:
            self.apri_split()

    def apri_split(self):
        if self.player is None or self.pip_window is not None or self.isFullScreen():
            return
        try:
            self.player2 = MpvVideo(self.video, options={"mute": "yes"})
            self.player2.imposta("volume", self.volume.get())
            self.player2.imposta("audio-device", self.sessione.config.get("audio_device", "auto"))
            self.player2.installEventFilter(self)
            self.player_layout.addWidget(self.player2, 1)
            self.player2.evento.connect(lambda evento, p=self.player2: self._evento_player(p, evento))
            self.split = True
            self.schermo_attivo = 0
        except Exception as errore:
            self.player2 = None
            self.riga_stato.setText("Split screen failed: " + str(errore))

    def chiudi_split(self):
        if not self.split:
            return
        self.schermo_attivo = 0
        self.split = False
        self.player2.ferma()
        self.player_layout.removeWidget(self.player2)
        self.player2.chiudi()
        self.player2.setParent(None)
        self.player2.deleteLater()
        self.player2 = None

    def pip_si_no(self):
        if self.pip_window is not None:
            self.esci_pip()
            return
        if not self.player or not self.file_in_onda:
            return
        try:
            posizione = float(self.player.leggi("time-pos") or 0)
            self.player.pausa(True)
            self.pip_window = QDialog(self, Qt.Tool | Qt.WindowStaysOnTopHint)
            self.pip_window.setWindowTitle("XVB")
            layout = QVBoxLayout(self.pip_window)
            layout.setContentsMargins(0, 0, 0, 0)
            self.player_pip = MpvVideo(self.pip_window)
            layout.addWidget(self.player_pip)
            self.player_pip.apri(self.file_in_onda)
            if posizione:
                self.player_pip.seek(posizione)
            self.pip_window.resize(480, 270)
            self.pip_window.finished.connect(self._pip_finestra_chiusa)
            self.pip_window.show()
        except Exception as errore:
            self.riga_stato.setText("Picture in picture failed: " + str(errore))
            self.esci_pip()

    def _pip_finestra_chiusa(self, *_):
        if not self._chiudendo_pip:
            self.esci_pip(chiudi_finestra=False)

    def esci_pip(self, chiudi_finestra=True):
        if self.pip_window is None:
            return
        finestra, player = self.pip_window, self.player_pip
        self.pip_window = None
        self.player_pip = None
        self._chiudendo_pip = True
        posizione = 0.0
        if player:
            try:
                posizione = float(player.leggi("time-pos") or 0)
                player.chiudi()
            except Exception:
                pass
        if chiudi_finestra:
            finestra.close()
        finestra.deleteLater()
        self._chiudendo_pip = False
        if self.player:
            if posizione:
                self.player.seek(posizione)
            self.player.pausa(False)

    def _posiziona_overlay(self):
        if self._overlay_attivo and self.barra.parent() is self.video:
            self.barra.setGeometry(
                0, max(0, self.video.height() - self.barra.height()),
                self.video.width(), self.barra.height())
            self.barra.raise_()

    def _attiva_overlay(self):
        if not self._overlay_attivo:
            self._overlay_attivo = True
            self.barra.setParent(self.video)
            self.barra.setAttribute(Qt.WA_StyledBackground, True)
            self.barra.setStyleSheet(self._stile_barra())
            for widget in self.barra.findChildren(QWidget):
                widget.installEventFilter(self)
            self.video.installEventFilter(self)
            self._posiziona_overlay()
        self.barra.show()
        self._mostra_overlay()

    def _disattiva_overlay(self):
        self._timer_overlay.stop()
        if not self._overlay_attivo:
            return
        self._overlay_attivo = False
        self.barra.setParent(self._centrale)
        self.barra.setStyleSheet(self._stile_barra())
        self._layout_principale.insertWidget(2, self.barra)
        self.barra.show()

    def _mostra_overlay(self):
        if not self._overlay_attivo:
            return
        self._posiziona_overlay()
        self.barra.show()
        self.barra.raise_()
        if self.isFullScreen() or (self.sinistra.isHidden() and self.destra.isHidden()):
            self._timer_overlay.start(3000)
        else:
            self._timer_overlay.stop()

    def _nascondi_overlay(self):
        if not self._overlay_attivo or not self.barra.isVisible():
            return
        if not self.isFullScreen() and (self.sinistra.isVisible() or self.destra.isVisible()):
            self._timer_overlay.stop()
            return
        if self.barra.frameGeometry().contains(QCursor.pos()):
            self._timer_overlay.start(3000)
            return
        self.barra.hide()

    def schermo_intero(self):
        if self.split:
            self.chiudi_split()
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().show()
            sinistra, destra = getattr(self, "_sidebar_prima", (True, True))
            self.sinistra.setVisible(sinistra)
            self.destra.setVisible(destra)
            self.maniglia_sx.setVisible(sinistra)
            self.maniglia_dx.setVisible(destra)
            self._sidebar_prima = None
            self.riga_stato.parentWidget().show()
            self._aggiorna_overlay_pannelli()
        else:
            self._sidebar_prima = (self.sinistra.isVisible(), self.destra.isVisible())
            self.menuBar().hide()
            self.sinistra.hide()
            self.destra.hide()
            self.maniglia_sx.hide()
            self.maniglia_dx.hide()
            self.riga_stato.parentWidget().hide()
            self.showFullScreen()
            self._attiva_overlay()

    def closeEvent(self, evento):
        player = self._attivo()
        if player and self.file_in_onda and os.path.isabs(self.file_in_onda):
            try:
                posizione = float(player.leggi("time-pos") or 0)
                durata = float(player.leggi("duration") or 0)
                if durata > 0:
                    cfg = self.sessione.config
                    posizioni = cfg.setdefault("posizioni", {})
                    durate = cfg.setdefault("durate", {})
                    if durata - posizione < 20:
                        posizioni.pop(self.file_in_onda, None)
                        durate.pop(self.file_in_onda, None)
                    else:
                        posizioni[self.file_in_onda] = round(posizione, 1)
                        durate[self.file_in_onda] = round(durata, 1)
                    scrivi_config(cfg)
            except Exception:
                pass
        self._timer_overlay.stop()
        self._timer_spegnimento.stop()
        self._timer_avviso.stop()
        if self._versione_worker and self._versione_worker.isRunning():
            self._versione_worker.wait(12000)
        if self._worker_copertine and self._worker_copertine.isRunning():
            self._worker_copertine.requestInterruption()
            self._worker_copertine.wait(25000)
        for worker in self._subtitle_workers:
            if worker.isRunning():
                worker.wait(45000)
        self.tendina.chiudi()
        self._timer_player.stop()
        self._timer_carico.stop()
        self._timer_volume.stop()
        self._timer_rec.stop()
        self._timer_dischi.stop()
        for worker in self.__dict__.get("_scan_workers", []):
            if worker.isRunning():
                worker.wait(30000)
        for worker in list(self._durata_workers):
            if worker.isRunning():
                worker.wait(16000)
        self._timer_info.stop()
        if self.registrando:
            self.ferma_registrazione()
        self._timer_refresh.stop()
        self._timer_epg.stop()
        self._timer_mpris.stop()
        if self._worker_liste and self._worker_liste.isRunning():
            self._worker_liste.wait(35000)
        for worker in self._stream_workers:
            if worker.isRunning():
                worker.wait(12000)
        if self._thread_epg.isRunning():
            self._thread_epg.wait(65000)
        for worker in self._logo_threads + self._cover_threads:
            if worker.isRunning():
                worker.wait(12000)
        if self._artist_worker and self._artist_worker.isRunning():
            self._artist_worker.requestInterruption()
            self._artist_worker.wait(20000)
        self._via_url_temporanei()
        scrivi_config(self.sessione.config)
        self.artwork_artista.salva_cache()
        scrivi_tag(self.tag_cache)
        if self.pip_window is not None:
            self.esci_pip()
        if self.player2:
            self.player2.chiudi()
            self.player2 = None
        if self.player:
            self.player.chiudi()
        super().closeEvent(evento)
