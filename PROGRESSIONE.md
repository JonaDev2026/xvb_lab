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
- [x] Nota storica superata: il branch ora contiene `main.py`, `engine/` e `ui/`; la prima integrazione Qt6 è presente ma non ancora collaudata.

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


## Avanzamento migrazione UI e playback Qt6

- [x] Separati i widget derivati dalla Stable in moduli dedicati: `ui/search.py` (Ricerca/Cursore), `ui/dialogs.py` (Finestrella/Tendina), `ui/list.py` (Elenco e delegate), `ui/guide.py` (Guida EPG).
- [x] Ridotto `ui/widgets.py` a facciata di compatibilità, mantenendo gli import già usati dalla finestra principale.
- [x] Aggiunta `ui/sidebar.py` per l'albero Qt6 con API di inserimento, cancellazione, selezione, espansione, tag e valori; collegato alla finestra principale.
- [x] Collegati nella sidebar IPTV > EPG/M3U > playlist > categorie, cartelle Local, dischi, CD/DVD, registrazioni, preferiti IPTV/Music/Video, media importati e sottocartelle.
- [x] Collegati alla finestra principale i controlli di trasporto con icone originali, seek orizzontale, volume con il widget Cursore, repeat tramite Tendina e orologio locale nella barra di stato.
- [x] Collegata Finestrella per le richieste di URL, apertura URL e pianificazione registrazioni.
- [x] Collegata la Guida Qt6 al metodo di apertura canale della finestra principale; aggiunti tick orari e indicatore dell'ora corrente.
- [x] Aggiunto il segnale di selezione mancante a Elenco e mantenuta la compatibilità MPRIS del cursore volume (`value()`/`setValue()`).
- [x] Completato il ciclo eventi di `engine/mpv.py` e impostato il framebuffer OpenGL RGBA8 nel rendering Qt.
- [x] Collegato il pulsante Favorite della barra alla gestione dei preferiti già presente nel controller; supporta i file locali e le sorgenti presenti nelle playlist.
- [ ] Confrontare ancora tutti i widget, i menu, i flussi e i metodi applicativi contro la Stable 4.4.4, senza dichiarare equivalenza prima del confronto.
- [ ] Completare il porting dei metodi rimanenti della classe `TV` e le decorazioni/overlay originali della barra.
- [ ] Verificare il rendering libmpv e tutti i flussi su X11 e Wayland.
- [ ] Collaudo completo e test di parità funzionale con la Stable.

Questi trasferimenti sono presenti nel branch, ma non sono stati eseguiti test in questa fase. Non è ancora la build da sottoporre al pull di collaudo.

## Migrazione Qt6 — aggiornamento

La struttura Qt6 è ora presente nel repository e non va più descritta come assente: `main.py`, `engine/mpv.py`, `ui/main_window.py`, `ui/sidebar.py`, `ui/search.py`, `ui/list.py`, `ui/guide.py` e `ui/dialogs.py` sono già stati creati. Questo non equivale ancora a una migrazione completa o a una parità verificata.

- Il motore `engine/mpv.py` usa `QOpenGLWidget` e libmpv Render API. Il rendering ora interroga `mpv_render_context_update` prima di disegnare il frame; restano da verificare inizializzazione e riproduzione su X11 e Wayland.
- La finestra principale Qt6 dispone già dei pannelli laterali da 300 e 220 px, area video, barra comandi da 96 px, barra di stato da 28 px e menu Media/Playback/Video/Audio/IPTV/View/Help. La disposizione e tutti i flussi devono ancora essere confrontati con la Stable.
- I widget `Ricerca`, `Cursore`, `Guida`, `Tendina`, `Elenco` e `Finestrella` hanno implementazioni Qt6. Sono stati riallineati alcuni colori della guida, della lista, dei menu popup e della finestra principale alla palette originale.
- La guida mantiene la finestra temporale di sei ore, righe da 64 px, colonna nomi da 250 px, intestazione da 28 px, sincronizzazione degli scorrimenti e aggiornamento ogni 30 secondi. Sono stati ripristinati scorrimento orizzontale con Shift e apertura del canale solo cliccando su un programma.
- La lista Qt6 mantiene l'API di compatibilità usata dalla finestra principale, la selezione singola, loghi/pallini, sottotitoli, poster e barre di avanzamento. Corretta la cancellazione multipla per non usare indici obsoleti.
- La finestra `Finestrella` ora dimensiona l'altezza sul contenuto; il tema dei dialoghi e della tendina usa i colori definiti dalla Stable.
- Aggiunti test di regressione per la cancellazione multipla della lista e per l'altezza del dialogo. Non eseguiti: il primo collaudo completo resta rinviato al pull concordato.

Commit di questo avanzamento: `b2aee4c`, `7adaee1`, `28c5594`, `505c33b`, `4fb96d9`, `f5ab422`, `55ebe0f`.

Restano aperti il confronto puntuale con i widget originali, l'integrazione completa dei flussi applicativi, la verifica del motore video e la parità funzionale dell'intera Stable.

## Controlli e collegamenti Qt6 — aggiornamento successivo

- La barra comandi ora può essere spostata sopra il video sia a schermo intero sia quando entrambe le barre laterali sono chiuse. Il timer la nasconde dopo tre secondi e il movimento del mouse la fa riapparire; il ridimensionamento video aggiorna la posizione dell'overlay.
- Lo stato delle due barre laterali viene conservato entrando e uscendo dal fullscreen. Il comando Playlists le mostra/nasconde insieme, come il comando originale; il menu View permette anche di intervenire separatamente.
- Ripristinate le scorciatoie originali principali: M, +/-, volume su/giù, cambio canale con sinistra/destra, seek con Shift+sinistra/destra, PageUp/PageDown, F11 ed Escape. I tasti non vengono sottratti ai campi di testo o ai pannelli ad albero.
- La lista canali conserva la riga del canale in riproduzione evidenziata senza sovrapporre la selezione blu; il cambio canale aggiorna l'indicatore.
- Ripristinati i controlli di ritardo audio per singolo contenuto, ritardo e dimensione sottotitoli con salvataggio delle preferenze, reset dei sottotitoli, selezione dispositivo di uscita audio tramite `audio-device-list` di libmpv e applicazione del dispositivo al secondo player split.
- Aggiunto accesso strutturato ai nodi libmpv (`MPV_FORMAT_NODE`) per leggere le liste dei dispositivi audio.
- Ripristinati il controllo release GitHub, il collegamento al download, la donazione e l'opzione Sempre in primo piano.
- La guida ora conserva la posizione di scorrimento durante il refresh, mostra il pallino colorato quando manca il logo e apre il canale solo cliccando su un blocco programma.
- Corretta la lista per rispettare il colore originale del canale e l'evidenziazione del programma/canale in onda.
- Aggiunti test di regressione per selezione tastiera, riga in onda, lifecycle overlay, cancellazione multipla e dimensionamento dialogo. Non eseguiti: il collaudo locale resta rinviato al pull concordato.

Commit recenti: `e24763c`, `16fc99a`, `14ca9fd`, `4837a37`, `5e53165`, `0078d03`, `0569cec`, `e95aece`, `45bf581`, `2884c01`, `f720f9e`, `f8ad1c5`, `4ab189d`, `49d8fb3`, `4202571`, `dd0b2ae`.

Il primo insieme dei quattro blocchi richiesti è stato implementato a livello di struttura e collegamenti Qt6, ma non è dichiarato completo: restano confronto puntuale con la Stable, verifica reale libmpv su X11/Wayland e controllo end-to-end di playlist, IPTV, EPG e libreria. Nessun pull di collaudo è richiesto in questo aggiornamento.

## Funzioni player e menu — completamento del trasferimento Qt6

- Aggiunta la gestione dei capitoli mpv: voci Previous/Next e menu dei capitoli con titolo, tempo e spunta sul capitolo attivo; le voci restano nascoste quando il contenuto non ha capitoli.
- Ripristinati i menu Repeat off / Repeat one / Repeat all con stato selezionato collegato alla configurazione.
- Ripristinati i controlli video della Stable: proporzioni, crop/panscan, deinterlacciamento, decodifica hardware, luminosità, contrasto, saturazione e reset. I valori sono salvati nelle chiavi globali originali; rimosse le sovrascritture video per-file che non appartengono al comportamento Stable.
- Ritardo audio salvato per URL come nella Stable; ritardo e dimensione sottotitoli restano controlli temporanei e non vengono salvati per-file.
- Aggiunta l'integrazione OpenSubtitles in un modulo separato `integrations/opensubtitles.py`: login, ricerca per titolo/lingua, elenco risultati, download, estrazione sicura del sottotitolo dall'archivio e caricamento in mpv. Le credenziali sono salvate nel percorso originale con permessi 0600.
- Aggiunto l'accesso libmpv `leggi_nodo` per le liste strutturate, usato sia per i dispositivi audio sia per i capitoli.
- I worker di verifica release e OpenSubtitles vengono gestiti in chiusura per evitare thread Qt lasciati attivi.

Questi trasferimenti ampliano i collegamenti del player, ma non sono ancora dichiarati verificati: test e prova d'uso completa verranno eseguiti dopo il pull concordato.

Ultimi commit successivi: `29e84b0`, `9429c66`, `8447a34`, `3cc2679`, `ba993b8`, `c15a13b`, `b5a2199`, `1125ba3`, `5aef256`, `c6ca98b`, `bac8c25`, `20faa8b`.
