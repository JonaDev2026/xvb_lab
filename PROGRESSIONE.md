# XVB Lab — Progressione

## Stato

Audit strutturale della Stable 4.4.4 completato: sorgente `xvb.py` del tag `v4.4.4`, 11.823 righe, 8 classi top-level e 400 metodi diretti nelle classi. L'elenco metodo-per-metodo è in [`analisi/METODI_STABLE_4.4.4.md`](analisi/METODI_STABLE_4.4.4.md); il riepilogo è in [`analisi/ANALISI_STABLE_4.4.4.md`](analisi/ANALISI_STABLE_4.4.4.md).

## Regole

- Stable 4.4.4 è il sorgente vincolante di codice, funzioni, logica e interfaccia.
- La UI Qt6 deve conservare struttura, proporzioni, controlli, menu, icone, colori e flussi della Stable.
- Le funzioni originali vanno trasferite senza omissioni, semplificazioni o placeholder.
- Il codice va organizzato in moduli separati mantenendo tracciabilità metodo originale/modulo Qt6.
- Rendering video con libmpv Render API e compatibilità X11/Wayland.

## Avanzamento verificato

- [x] Recuperato il sorgente ufficiale Stable 4.4.4.
- [x] Inventariate le 8 classi top-level.
- [x] Elencati i 400 metodi diretti con riga sorgente.
- [x] Inventariate anche tutte le 106 funzioni top-level con riga sorgente in `analisi/FUNZIONI_TOP_LEVEL_STABLE_4.4.4.md`.
- [x] Copiato `traduzioni.py` dalla Stable senza modifiche in `i18n/traduzioni.py` (1.418 righe, sette lingue).
- [x] Aggiunta API `i18n` separata dal toolkit grafico, con inglese predefinito.
- [x] Rilevati i punti originali di costruzione menu, pannelli, fullscreen e overlay.
- [ ] Mappatura completa delle dipendenze e assegnazione di ogni metodo/funzione al modulo Qt6.
- [x] Trasferite in `core/media.py` le funzioni originali di classificazione media, URL, scansione cartelle e formattazione durata.
- [x] Trasferite in `core/config.py` le directory applicative e la persistenza JSON, inclusa la compatibilità con la vecchia configurazione TV.
- [x] Trasferiti in `core/playlists.py` rilevamento playlist, categorie, download/cache M3U, parsing canali, EPG IDs, loghi e chiavi ClearKey, mantenendo la logica della Stable.
- [x] Trasferiti in `core/epg.py` parsing XMLTV e gzip, conversione orari/fusi, cache guide, unione programmi e guide, identificazione canali, icone programma e raggruppamento registrazioni.
- [x] Trasferita in `core/favorites.py` la gestione originale dei preferiti IPTV/Music/Video, inclusa compatibilità con `favorite.m3u` precedente, categorie, ID e chiavi ClearKey.
- [x] Aggiunti test di regressione per salvataggio, lettura, metadati e rinomina del vecchio file preferiti.
- [x] Trasferiti in `core/constants.py` i metadati e i parametri originali della Stable 4.4.4.
- [x] Trasferiti in `core/log.py` logging rotante, filtro per oscurare credenziali e token, gestione delle eccezioni globali e dei thread; il callback GUI è predisposto per Qt.
- [x] Trasferita in `core/image.py` la premoltiplicazione alfa richiesta dalle sovrapposizioni mpv.
- [x] Trasferiti in `core/metadata.py` estrazione titolo/anno, lettura metadati da percorso musicale, cache JSON, download HTTP con User-Agent XVB, copertine incorporate e ricerca poster locali.
- [x] Trasferiti in `core/tags.py` lettura/scrittura della cache tag e accesso Mutagen con cache per percorso e data modifica.
- [x] Aggiunti test per lettura tag, cache e fallback su file mancanti.
- [x] Trasferiti in `core/colors.py` conversione SVG, schiarimento colori, estrazione colore dominante dai loghi, cache colori versione 4 e scelta icone playlist.
- [x] Aggiunti test per cache colori, conversione SVG e priorità icone.
- [x] Trasferite in `core/artwork.py` le primitive PIL originali per copertine vinile, maschere e anelli, pallini, qualità, cartelle, segnalibri, globo, dischi e icone vinile.
- [x] Le primitive producono immagini RGBA PIL, pronte per l'adattatore QImage/QPixmap Qt; la geometria e i colori derivano dalla Stable.
- [x] Trasferiti in `core/discs.py` rilevamento dischi ISO/UDF montati, verifica conservativa cifratura DVD CSS, rilevamento CD audio via udev, riconoscimento DVD e pulizia etichette disco.
- [x] Aggiunti test per riconoscimento CD/DVD, etichette e gestione prudenziale di VOB non leggibili.
- [x] Trasferita in `core/thumbnails.py` la generazione delle anteprime locali: priorità poster/cover, copertine incorporate nei brani, fotogrammi ffmpeg, cache basata su percorso e data modifica.
- [x] Aggiunti test di regressione per dimensioni, trasparenza, icone e fasce di qualità; CI installa Pillow.
- [x] Aggiunti test per i casi titolo/anno, struttura cartelle musicali, poster e cache JSON.
- [x] Trasferita in `integrations/mpris.py` l'integrazione MPRIS originale: comandi multimediali, metadati, posizione, volume, shuffle e repeat; i callback dal bus D-Bus vengono inoltrati al thread Qt tramite segnale queued, senza `root.after` Tkinter.
- [x] Aggiunti test per il filtro di sicurezza dei log.
- [x] Trasferiti in `core/stream.py` parsing ClearKey (singola chiave, coppia KID/KEY e JSON), esclusione delle chiavi nulle, pulizia manifest DASH e proxy HTTP locale per manifest live.
- [x] Aggiunti test di regressione per ClearKey e manifest DASH.
- [x] Aggiunto workflow GitHub Actions per eseguire automaticamente i test core a ogni push e pull request.
- [x] Aggiunti test di regressione per conversione XMLTV, fusione guide, confronto versioni e normalizzazione nomi.
- [x] Aggiunti test di regressione per formati media, scansione file, categorie preferiti, rilevamento M3U e parsing dei metadati.
- [ ] Migrazione dei restanti moduli applicativi in Qt6.
- [ ] Ricostruzione della UI originale in Qt6.
- [ ] Integrazione e verifica libmpv Render API su X11 e Wayland.
- [ ] Test di parità funzionale con Stable.

Nessuna funzione è ancora dichiarata migrata e l'applicazione non è pronta per il test. La vecchia implementazione Lab non è la base funzionale.

- [x] Trasferita in `core/stream.py` la selezione delle varianti HLS master della Stable: risoluzioni, bitrate, gruppi audio esterni, URL assoluti e master ricostruito per mpv.
- [x] Aggiunti test per master HLS multi-qualità, audio separato, playlist non master, errori di rete e host escluso `jmp2.uk`.
- [x] Trasferita in `core/recordings.py` la presentazione delle registrazioni raggruppate per canale/giorno e il confronto numerico delle versioni.
- [x] Trasferita in `core/colors.py` la fusione del colore dei programmi EPG con lo sfondo, mantenendo il fallback della Stable.
- [x] Aggiunti test per registrazioni, confronto versioni e colori dei programmi EPG.

- [x] Trasferita in `core/artwork.py` la premoltiplicazione alfa richiesta dalle sovrapposizioni libmpv, mantenendo la trasformazione RGBA della Stable.
- [x] Aggiunto test numerico sui canali colore e alfa semitrasparenti.

- [x] Integrate in `core/constants.py` le costanti originali della Stable 4.4.4 per velocità, proporzioni, buffer visivi, palette, stati e dimensioni dell'elenco.
- [x] Trasferite in `core/metadata.py` le ricerche MusicBrainz/Cover Art Archive per copertine di album e brani, con priorità alle pubblicazioni ufficiali e agli album.
- [x] Trasferita in `core/system.py` la rilevazione del font desktop originale per GNOME, Cinnamon, XFCE e KDE.
- [x] Aggiunti test di regressione per selezione copertine MusicBrainz e rilevamento font desktop.

- [x] Trasferiti in `core/system.py` i parametri tipografici originali e la risoluzione dei due formati di file Google Sans inclusi nella Stable.

- [x] Trasferita la ricerca TMDB della Stable: generi film/serie con cache per lingua e metadati con priorità al risultato provvisto di poster.
- [x] Aggiunti test per cache generi, selezione poster e fallback tra ricerca film e serie.
- [x] Corretto `PROGETTO.md`: il branch attuale non contiene ancora `main.py`, `engine/` o `ui/`; non viene più riportata come verificata una base Qt6 che non è presente nel repository.

- [x] Avviata la migrazione Qt6 dei widget visuali originali in `ui/widgets.py`: casella di ricerca Material con lente, segnaposto, callback ed Escape; cursore percentuale con trascinamento, rotella, callback e sfondo dinamico. Le API conservano i nomi originali `Ricerca` e `Cursore`.
- [ ] Verificare la parità grafica dei widget Qt6 con la Stable e completare i widget `Guida`, `Tendina`, `Elenco` e `Finestrella`.


## Prima integrazione Qt6

- [x] Creato `engine/mpv.py`: istanza libmpv tramite API C, rendering OpenGL con `mpv_render_context` dentro `QOpenGLWidget`, caricamento file/URL, play/pausa, stop, seek e volume.
- [x] Creato `ui/main_window.py`: finestra 1280×720 con pannello sinistro da 300 px, video centrale, pannello destro da 220 px, barra comandi da 96 px e stato da 28 px; menu principali Media, Playback, Video, Audio, IPTV, View e Help.
- [x] Collegata la sessione alle funzioni originali di playlist e guida in `core/session.py`: caricamento liste configurate, categorie M3U, canali e guide XMLTV.
- [x] Caricamento EPG eseguito in un thread Qt separato; le sorgenti remote passano dalla cache originale `prendi_epg`.
- [x] Collegate alla finestra Qt le selezioni playlist/categoria, ricerca canali, apertura singolo canale, importazione cartelle locali, guida EPG e controlli mpv per playback, velocità, ripetizione, aspect ratio, deinterlacciamento, decodifica hardware, regolazioni video e tracce audio/sottotitoli.
- [x] Migrati in `ui/widgets.py` i componenti Qt6 con API compatibili: `Ricerca`, `Cursore`, `Tendina`, `Elenco`, `Finestrella` e `Guida`.
- [x] Aggiunto `main.py` come punto di avvio e `requirements.txt` per PySide6, Pillow e Mutagen.
- [x] Aggiunti test smoke Qt6 e compilazione moduli nel workflow CI.

### Stato effettivo

La prima integrazione Qt6 esiste nel branch, ma non è ancora una migrazione completa e non è pronta per il pull di collaudo. La compatibilità grafica e comportamentale dei widget non è stata verificata contro la Stable; l'elenco Qt6 non ha ancora tutte le decorazioni dinamiche originali (loghi, poster, progressi e tag); restano da trasferire le classi applicative e i metodi di `TV`, l'intero flusso di playlist/EPG/registrazioni, le funzioni di libreria musicale e video, i menu dinamici e le interazioni complete. Il rendering libmpv è stato collegato a livello di codice, ma non verificato su X11/Wayland. Nessun test viene dichiarato superato finché CI e prova reale non lo confermano.
