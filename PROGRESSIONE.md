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

## Rifinitura widget lista Qt6

- Corretto il dimensionamento delle righe di `Elenco`: ora considera anche l'altezza del poster limitato alla sola riga del canale in onda, non soltanto il poster globale.
- Quando cambia l'altezza dei poster, la lista ricalcola le dimensioni effettive degli elementi e il layout, così lo spazio riservato al poster viene applicato anche allo scorrimento.
- La misura del delegate ora rispetta le righe senza sottotitolo, evitando di imporre sempre l'altezza minima delle righe a due linee.
- Rimosse importazioni circolari superflue in fondo a `ui/list.py`.

Non eseguiti test né prove grafiche: restano per il pull concordato.

## Layout e menu Qt6 — ulteriore allineamento

- Aggiunte le maniglie laterali originali da 8 px con tre puntini, cursore di ridimensionamento, limiti minimi/massimi e salvataggio delle larghezze `larga_sx` e `larga_dx`. Le maniglie seguono la visibilità dei rispettivi pannelli e spariscono in fullscreen.
- Corretto un problema strutturale: la barra comandi non era inserita nel layout verticale principale. Ora è presente tra area centrale e barra di stato; l'overlay la rimuove e la reinserisce nella stessa posizione quando viene disattivato.
- Il menu Playback ora offre Repeat off/one/all con stato, Previous/Next chapter e l'elenco dinamico dei capitoli mpv con orari e capitolo attivo.
- Aggiunta una verifica nel test Qt per controllare che la barra comandi appartenga al layout principale.
- Verificati a livello di sorgente gli import Qt necessari per maniglie e selettore dispositivi audio; non sono stati eseguiti test runtime.

## Finiture interfaccia — aggiornamento

- Aggiunte le maniglie di ridimensionamento laterale e collegate alle larghezze persistenti.
- Ripristinato il pannello avviso originale da 42 px, cliccabile e con chiusura temporizzata; gli avvisi di aggiornamento vengono mostrati qui e restano visibili finché non vengono chiusi.
- Corretto l'ordine del layout principale: contenuto, avviso, barra comandi da 96 px, stato da 28 px. L'overlay fullscreen rimuove e reinserisce la barra nella posizione corretta.
- I test Qt ora controllano l'ordine della barra e dell'avviso nel layout; non sono stati eseguiti.

## Riproduzione in sequenza dei file locali

- Reintrodotto `prossimo_file()` della Stable: a fine file si passa alla voce successiva dell'elenco attivo; all'ultimo elemento si torna al primo soltanto con Repeat all; Repeat one riapre il file corrente.
- Collegato il fine-riproduzione del motore libmpv a questa sequenza per i percorsi locali, mantenendo il comportamento di cambio canale Repeat all per gli stream.
- La sequenza usa l'ordine effettivo di `_canali_visibili`, quindi rispetta playlist, categoria e filtro attivi.

Non eseguiti test o prove con libmpv; il comportamento resta da verificare al pull.

## Loop A-B del player

- Ripristinati i tre comandi originali: imposta punto A, imposta punto B e azzera.
- Il loop è associato al contenuto corrente; B deve essere successivo ad A. Il timer di sincronizzazione libmpv riporta la posizione ad A quando raggiunge B.
- Inseriti i comandi nel menu Playback e mantenuti i messaggi localizzati tramite il catalogo Stable.

Non eseguiti test né verifiche di riproduzione.

## Drag & drop e timer di spegnimento

- Aggiunto il supporto Qt6 per trascinare file, cartelle e playlist sulla finestra.
- Le cartelle multimediali vengono aggiunte alla libreria, i file multimediali all'elenco importati o alla cartella già registrata, le playlist M3U vengono aggiunte alla configurazione e ricaricate.
- Ripristinato il timer di spegnimento con scelte da 15 a 120 minuti, annullamento e arresto della sola riproduzione alla scadenza.
- Il timer viene fermato durante la chiusura dell'applicazione.
- Ripristinata la scelta della velocità di riproduzione con salvataggio della preferenza.

Non eseguiti test né prove d'uso. Il drag & drop misto (playlist insieme a cartelle e file nello stesso rilascio) resta da rifinire.

- Rifinito il rilascio misto: ora cartelle, file multimediali e playlist M3U nello stesso trascinamento vengono registrati in configurazione e ricaricati senza perdere le cartelle/importazioni già presenti.

## Asset originali della Stable

- Aggiunto un workflow che recupera dal tag immutabile `v4.4.4` del repository originale la cartella completa `icone/`, i font e `icon.png`, poi li registra nel repository Lab.
- In questo modo la UI Qt6 usa gli stessi file grafici e font della Stable, senza ricrearli o sostituirli con icone provvisorie.
- Il workflow è automatico su push in `main` e può anche essere avviato manualmente.

Il completamento del trasferimento degli asset dipende dall'esecuzione del workflow GitHub; non ho ancora verificato il risultato.

## Sfondo del lettore e foto artista

- Aggiunto `ui/backdrop.py`: widget Qt6 che disegna l'immagine centrata mantenendo le proporzioni.
- Il video resta sul widget libmpv; a player fermo viene mostrata l'immagine `icone/screen.png`; per i file audio vengono usate prima la foto artista in cache e poi la copertina del brano.
- Migrata in `core/artist_artwork.py` la cache persistente degli artisti e la ricerca TheAudioDB con confronto del nome, cache negativa di sette giorni e salvataggio JPEG.
- Il precaricamento delle foto avviene in un QThread, con pause fra le richieste; il thread viene interrotto e atteso in chiusura.
- Il layout video ora separa lo sfondo dal contenitore dei player, così il secondo player dello split mantiene la disposizione affiancata.

Non eseguiti test grafici o prove di rendering. La dissolvenza originale dello sfondo resta da trasferire.

## Verifica CI dopo l'integrazione Qt6

- Il workflow ha trasferito nel Lab gli asset originali della Stable 4.4.4: `icone/`, `fonts/` e `icon.png`. I riferimenti Git degli asset principali corrispondono a quelli del tag Stable.
- Corretto l'import del percorso applicazione nel widget di sfondo: `QUI` proviene da `core.config`.
- GitHub Actions: compilazione dei moduli e suite di regressione concluse con esito positivo; 78 test superati, inclusi test Qt per dialoghi, tendina, guida, lista, ricerca, cursore e costruzione della MainWindow senza libmpv.
- Questa CI non sostituisce la prova reale di rendering libmpv, riproduzione e confronto grafico su X11/Wayland.


- Rifinito lo sfondo: cache delle immagini per evitare ricaricamenti a ogni aggiornamento del player e dissolvenza Qt6 da 1,2 secondi con attesa iniziale, come nella Stable.
- Ripristinato anche il pulsante contestuale della velocità: nascosto a x1, compare quando viene selezionata una velocità diversa e cicla nello stesso ordine della Stable.

## Eventi libmpv e gestione degli errori

- Collegati gli eventi END_FILE dei due player Qt6.
- Il completamento di un file locale richiama la sequenza successiva; gli errori di stream fanno avanzare il canale con limite di tentativi, azzerato quando la riproduzione riprende.
- Ripristinata la gestione specifica dei DVD non riproducibili, senza saltare automaticamente a un altro contenuto.
- In caso di errore persistente viene mostrato lo sfondo invece di lasciare il riquadro del video in stato nero.

- Ripristinato l'indicatore di buffering animato nella barra di stato: usa l'icona originale `loading.png`, ruotata ogni 50 ms quando libmpv segnala `paused-for-cache`.

- Ripristinata la tinta del canale nella progress e nella sfumatura della barra comandi; il cursore volume riceve la stessa sfumatura sottostante. A riproduzione ferma la barra torna al colore neutro.

- La barra comandi Qt6 è ora sovrapposta al video anche nella finestra normale, come nella Stable; resta visibile con i pannelli laterali aperti e si nasconde dopo tre secondi quando entrambi sono chiusi o a schermo intero. In PiP torna al layout esterno.
- La sfumatura colorata del canale viene mantenuta anche nella barra sovrapposta semitrasparente.

- Aggiornato il test Qt della finestra principale per verificare la nuova collocazione della barra in overlay nel layout normale, invece della vecchia barra esterna.

- Allineata la barra overlay alle coordinate originali: altezza 96 px, progress a y=30 e riga comandi da y=38.

- Riordinati i comandi della barra secondo la Stable: preferito, fullscreen, PiP, velocità, qualità (solo quando ci sono varianti), playlist, volume e muto. Rimosso il pulsante Split aggiuntivo: la funzione resta nel menu View e nella scorciatoia F2.

- Ripristinato il cursore volume a comparsa: inizialmente collassato, si espande passando sul pulsante muto o sul cursore, si richiude dopo 400 ms e anima l'apertura/chiusura in cinque passi da 15 ms.

- Il motore libmpv ora usa la cartella e il modello nome file per gli screenshot della Stable (`~/Pictures/xvb/xvb-...`) e scollega esplicitamente il callback di aggiornamento OpenGL prima di liberare il contesto render.

- Il precaricamento delle foto artista ora interrompe anche le pause fra richieste quando si chiude il player; l'attesa di chiusura resta limitata al timeout massimo della richiesta in corso.

- Ripristinate le icone contestuali di volume (muto, zero, basso, medio, alto) e repeat (file/playlist), con tooltip aggiornato allo stato attivo.

- Ripristinato il comportamento Stop/Resume: Stop conserva tipo, nome, percorso e ID del contenuto corrente; Play dopo Stop riapre lo stesso contenuto dall'inizio, con tooltip Resume.
- Stop annulla anche il timer di spegnimento e conclude un'eventuale registrazione attiva.

- Il pulsante Shuffle ora riflette visivamente lo stato attivo e aggiorna tooltip e stato check anche quando il valore arriva da MPRIS.


## Scansione cartelle locali Qt6

- La scelta di una cartella da Media > Open folder non esegue più `media_in()` sul thread grafico: la scansione filesystem viene eseguita da `_ScansionaCartella(QThread)`.
- Il risultato viene consegnato al thread Qt tramite segnale; la finestra aggiorna la libreria, la sidebar e l'elenco soltanto al termine della scansione.
- La routine `_media_locale` accetta anche il risultato già raccolto dal worker, evitando una seconda scansione della stessa cartella.
- I worker vengono attesi durante la chiusura della finestra per evitare thread Qt ancora attivi.
- La lettura dei tag e la preparazione dei sottotitoli restano da ottimizzare in un worker dedicato; il percorso drag-and-drop delle cartelle deve ancora essere portato sullo stesso flusso asincrono.

Commit: `aebfa92`. Nessun test runtime eseguito.

- Completata la prima sincronizzazione degli asset originali; il workflow è stato lasciato manuale per evitare download e commit ripetuti a ogni push.


## Scansione asincrona anche per drag & drop

- Il rilascio di più cartelle sulla finestra ora usa un worker Qt dedicato per scandire tutte le cartelle in background.
- I risultati vengono consegnati insieme al termine della scansione; file singoli e playlist trascinati nello stesso rilascio mantengono il flusso di importazione già presente.
- Il ciclo di vita del worker riutilizza la gestione di chiusura già aggiunta per le scansioni avviate da Open folder.
- La preparazione dei metadati/tag avviene ancora dopo la scansione e resta da separare dal thread grafico per librerie molto grandi.

Commit: `b3f2b68`. Nessun test runtime eseguito.


- Ottimizzata anche la preparazione dei metadati locali: lettura dei tag audio, fallback dai percorsi, titoli/anni video e sottotitoli Music/Video avvengono ora nei worker di scansione, non nel thread grafico.
- Il risultato trasferito alla UI contiene già nome, percorso, categoria e sottotitolo; la finestra non ripete la lettura dei tag né la scansione filesystem.
- La stessa preparazione viene usata sia da Open folder sia dal drag & drop multiplo.

Commit: `c689417`. Nessun test runtime eseguito.


## Caricamento librerie locali all'avvio

- Eliminata la scansione sincrona delle cartelle configurate dal costruttore della finestra principale.
- Le cartelle Local vengono ora scandite dopo la costruzione della UI, tramite il worker Qt già usato da Open folder e drag & drop.
- Anche lettura tag e preparazione delle righe Music/Video avvengono nel worker; al completamento vengono aggiornati una sola volta sidebar ed elenco.
- La finestra non resta bloccata all'avvio mentre attraversa librerie locali estese.

Commit: `19b6e1b`. Nessun test runtime eseguito.


## Ripresa e avanzamento file locali

- Ripristinata la memoria della posizione dei file locali: posizione e durata vengono salvate nella configurazione ogni dieci secondi, con salvataggio finale alla chiusura.
- A meno di venti secondi dalla fine la posizione viene cancellata, così la riproduzione successiva riparte dall'inizio.
- Il numero di posizioni memorizzate è limitato a 300, come nel comportamento Stable.
- All'evento libmpv `FILE_LOADED`, i file locali riprendono dalla posizione salvata quando restano più di venti secondi.
- Le barre di avanzamento dell'elenco ora mostrano anche il progresso dei file locali, oltre a quello dei programmi EPG.

Commit: `1d6b011`. Nessun test runtime eseguito.


- Le cartelle locali vengono ordinate alfabeticamente per titolo dopo la lettura dei tag, ripristinando l'ordine definitivo usato dalla Stable per Music e Video.

Commit: `6263f41`.


## Eventi libmpv — sottoscrizione esplicita

- Il motore Qt6 ora registra esplicitamente gli eventi libmpv necessari al ciclo player: START_FILE, END_FILE, FILE_LOADED, PLAYBACK_RESTART e SHUTDOWN.
- Questo rende effettiva la consegna degli eventi usati per avanzamento automatico, ripresa della posizione, aggiornamento del playback e chiusura del motore.

Commit: `a11fdc2`. La verifica runtime resta rinviata al pull concordato.


## Shuffle conforme alla Stable

- Lo shuffle ora riguarda soltanto gli elenchi di file locali, non i canali IPTV.
- Attivandolo, la lista locale viene mescolata una volta e il file in riproduzione resta in cima; navigazione successiva e riproduzione in sequenza seguono quell'ordine.
- Disattivandolo si torna all'ordine alfabetico originale. Il comportamento viene applicato anche quando la preferenza Shuffle era già attiva all'avvio e si apre una cartella locale.
- La navigazione IPTV resta sequenziale, come nella Stable.

Commit: `b799089`, `39cca51`. Nessun test runtime eseguito.


- Corretto il salvataggio della posizione per non interrompere il ciclo player quando la configurazione contiene dati non validi: il ripristino gestisce gli errori senza bloccare gli eventi libmpv.


## Inizializzazione della finestra e verifica CI

- Corretto l'ordine di inizializzazione dello stato del contenuto in riproduzione: `nome_in_onda`, `ide_in_onda` e `file_in_onda` vengono creati prima del primo popolamento dell'elenco.
- Rimossa la seconda inizializzazione successiva, che avrebbe potuto azzerare lo stato.
- GitHub Actions sul commit `05268c1` ha completato compilazione dei moduli e test di regressione/Qt con esito positivo.
- Il test di costruzione della `MainWindow` viene eseguito senza libmpv; il rendering reale e la riproduzione restano da verificare sul sistema Linux di prova.

Commit: `05268c1`.


## Aggiornamento automatico delle guide EPG

- Ripristinato il controllo periodico presente nella Stable 4.4.4: ogni 30 minuti vengono controllate le guide configurate.
- Le guide remote vengono ricaricate quando la cache manca o supera le sei ore; le guide locali vengono ricaricate quando il file cambia rispetto all'ultimo caricamento.
- Dopo un tentativo fallito o completato, un nuovo tentativo automatico non parte prima di un'ora; un caricamento già in corso non viene duplicato.
- Il controllo usa un helper isolato in `core/epg.py`, richiamato da un `QTimer` della finestra principale e fermato durante la chiusura.
- Aggiunti test per scadenza cache remota, modifica dei file locali e intervallo minimo fra i tentativi.
- GitHub Actions sul commit `aadc7d6` ha superato compilazione e suite di regressione/Qt.

Commit: `bad83bc`, `f2e96f0`, `7cbc8cc`, `c277eda`, `aadc7d6`.


## Ripristino della navigazione delle registrazioni

- I nodi canale/data dell'albero Registrazioni ora aprono l'elenco dei programmi registrati in quella giornata, come nella Stable; le singole registrazioni continuano ad aprirsi direttamente.
- L'elenco centrale mostra titolo e orario, mantiene la categoria di registrazione e usa il colore del canale registrato.
- Ripristinata la ricerca asincrona della durata dei file locali con `ffprobe`: quando una riga ha una posizione salvata ma manca la durata, la durata viene calcolata in un worker Qt e la barra di avanzamento viene ridisegnata.
- Gli stati necessari a lista e worker vengono inizializzati prima del primo aggiornamento grafico, evitando accessi prematuri durante il paint.
- Completato anche il trasferimento del nome originale contenuto nell'header gzip XMLTV nella configurazione; il nome di fallback della guida ora usa la stessa regola della Stable.
- Separato il controllo EPG dal timer delle playlist: il timer playlist non forza più un ricaricamento delle guide ogni 30 minuti; il controllo EPG dedicato rispetta la cache di sei ore e il limite di un'ora fra i tentativi.
- Aggiunti test Qt per la selezione dei gruppi di registrazioni, la richiesta asincrona della durata e l'inizializzazione anticipata degli stati. GitHub Actions sul commit `d05273e` ha superato compilazione e suite di regressione/Qt.

Commit: `e0d9104`, `dbbd49e`, `aae3fb8`, `4e2d5d3`, `e2d1ac8`, `631865e`, `6efe1ce`, `0ad0334`, `a1dff0d`, `a6b62e9`, `ecd4cf9`, `d05273e`.


## Integrazione MPRIS — aggiornamento e metadati

- Ripristinato l'aggiornamento periodico MPRIS ogni secondo, attivo soltanto quando il servizio DBus è disponibile e fermato durante la chiusura.
- I metadati locali includono titolo/tag e fallback dal percorso; per IPTV viene esposto il programma EPG corrente.
- L'immagine MPRIS privilegia la copertina del contenuto, poi la foto artista o il poster locale; per gli stream usa il logo in cache e infine l'icona applicazione.
- La chiamata `OpenUri` resta collegata all'apertura del contenuto e i comandi di trasporto continuano a passare dal dispatcher Qt.
- Aggiunto un test Qt per il timer, l'aggiornamento dello stato e l'arresto alla chiusura. GitHub Actions sul commit `aeb2978` ha superato compilazione e suite di regressione/Qt.

Commit: `60f8e2a`, `b35ab4c`, `9c133bc`, `757de30`, `aeb2978`.


## Avvio da file manager e istanza singola

- Ripristinato il socket Unix `xvb.sock` nel runtime utente (`XDG_RUNTIME_DIR`, con fallback in `~/.cache/xvb`) usando il protocollo della Stable 4.4.4.
- Una seconda istanza inoltra i percorsi alla finestra già aperta; senza argomenti porta semplicemente la finestra in primo piano.
- L'ascolto parte dopo il collegamento dei segnali alla finestra, così i file inviati durante l'avvio non vengono persi.
- `main.py` gestisce gli argomenti: una playlist M3U singola viene aggiunta e selezionata; file e cartelle vengono aperti tramite il flusso drag-and-drop già migrato.
- La chiusura arresta il socket e rimuove il file di runtime.
- Aggiunti test per inoltro file e riattivazione della finestra. GitHub Actions sul commit `2786e12` ha superato compilazione e suite di regressione/Qt (87 test).

Commit: `8a13358`, `ba3fb7f`, `c785c2a`, `f79da58`, `e076863`, `8f4a0ff`, `2786e12`.


## Completamento del flusso di avvio esterno

- La seconda istanza porta ora la finestra esistente in primo piano anche quando inoltra file o cartelle.
- Una playlist ricevuta da una seconda istanza viene selezionata dopo il ricaricamento, non soltanto aggiunta all'archivio.
- Il socket Unix viene chiuso con risveglio e join del listener; il ricevitore viene avviato solo dopo il collegamento dei segnali alla finestra, evitando la perdita di richieste durante la costruzione della UI.
- Al termine della sessione vengono rimossi i nomi e le copertine delle URL temporanee, svuotato `url_aperti` e salvata la configurazione, come nella Stable.
- Aggiunti test per selezione playlist esterna e pulizia delle URL temporanee. GitHub Actions sul commit `2c55359` ha superato compilazione e suite di regressione/Qt.

Commit: `5258042`, `dd25959`, `427a80c`, `6f12365`, `fc7e772`, `5d0eb61`, `603ce4a`, `2c55359`.


## Finestra guida EPG e rimozione guide

- La finestra TV Guide ora è unica: una seconda richiesta riporta in primo piano quella esistente; alla chiusura viene eliminata e può essere ricreata.
- La rimozione di una guida conserva il nome visualizzato prima di cancellare i metadati, così la riga di stato riporta il nome XMLTV effettivo e non il solo URL.
- Aggiunti test Qt per ciclo di vita della finestra guida e nome mostrato dopo la rimozione. GitHub Actions sul commit `3d4b525` ha superato compilazione e suite di regressione/Qt.

Commit: `bb2b853`, `89525ea`, `38480ad`, `d0e3817`, `ea1a835`, `3d4b525`.


## Aggiornamento periodico playlist

- Il controllo automatico delle playlist remote confronta ora il contenuto M3U prima e dopo il refresh, non il solo timestamp del file cache.
- Se la cache scade ma il server restituisce gli stessi byte, la libreria non viene ricaricata inutilmente; se il contenuto cambia o la cache viene creata, la sessione viene aggiornata.
- Aggiunti test per contenuto invariato con timestamp modificato e per contenuto effettivamente cambiato. GitHub Actions sul commit `4bd53e1` ha superato compilazione e suite di regressione/Qt.

Commit: `8182298`, `c1420ed`, `4bd53e1`.


## Coerenza dei dati EPG durante i refresh

- Prima di rileggere le guide vengono svuotate le cache globali delle icone programma, evitando che immagini associate a vecchi orari restino visibili.
- Se l'ultima guida viene rimossa o non resta alcuna guida configurata, nomi e programmi precedenti vengono azzerati.
- I refresh automatici sono silenziosi: se tutte le sorgenti non sono raggiungibili, l'ultima guida valida resta disponibile; un caricamento manuale senza guide valide azzera invece i dati.
- La finestra mantiene i dati EPG correnti fino al completamento del nuovo caricamento, evitando una schermata vuota durante il download.
- Aggiunti test per cache icone obsolete, rimozione dell'ultima guida e refresh silenzioso offline. GitHub Actions sul commit `1fb22e1` ha superato compilazione e suite di regressione/Qt.

Commit: `cb7ca50`, `aee97e1`, `79c21d0`, `15a08b1`, `0f4f605`, `bd31ee5`, `1fb22e1`.


## Registrazione DVD

- Il pulsante REC ora segue la regola della Stable: registra gli stream HTTP(S) e i DVD non cifrati; rifiuta i DVD protetti e non avvia registrazioni da normali file locali.
- Il controllo della protezione DVD usa `dvd_cifrato()` prima di impostare `stream-record` su libmpv.
- Aggiunti test Qt per DVD non cifrati e protetti. GitHub Actions sul commit `ab1d743` ha superato compilazione e suite di regressione/Qt.

Commit: `db89146`, `88fe27e`, `ab1d743`.


## Ripristino delle informazioni EPG nella barra di stato

- La barra di stato Qt6 mostra nuovamente l'orario del programma in onda, il titolo del programma successivo e il relativo orario, usando gli intervalli della guida XMLTV associata al canale effettivamente in riproduzione.
- Ripristinata anche la categoria IPTV del canale in onda; la categoria viene ricavata dalla voce M3U associata all'URL riprodotto e non dalla selezione corrente dell'elenco. Viene nascosta per file locali e quando la riproduzione viene fermata.
- Aggiunti test Qt per programma corrente/successivo e categoria attiva; GitHub Actions sul commit `57b66f8` ha superato compilazione e suite di regressione/Qt.

Commit: `6998665`, `beb8a9f`, `572e42a`, `57b66f8`.


## Stato del controllo REC

- Il pulsante REC della barra comandi ora passa all'icona `rec_stop.png` e al tooltip Stop durante la registrazione, tornando a `rec.png` e Record quando termina.
- Il comportamento è applicato sia alle registrazioni avviate manualmente sia a quelle pianificate, perché passa dai metodi comuni di avvio/arresto.
- Aggiunto test Qt sul cambio e ripristino dello stato del pulsante. GitHub Actions sul commit `b37b04e` ha superato compilazione e suite di regressione/Qt.

Commit: `ad03baa`, `b37b04e`.


## Navigazione tracce e capitoli nel menu Playback

- Ripristinate nel menu Playback le azioni Previous e Next, oltre ai comandi Previous chapter e Next chapter.
- Aggiunto il sottomenu Chapters, popolato dinamicamente dai capitoli esposti da libmpv e nascosto quando il contenuto non ne dispone.
- Il menu viene aggiornato all'evento FILE_LOADED; la lettura dell'indice corrente conserva correttamente il capitolo zero.
- Aggiunto test Qt per visibilità, popolamento e selezione del capitolo corrente. GitHub Actions sul commit `f18d97b` ha superato compilazione e suite di regressione/Qt.

Commit: `c01cd46`, `48dd002`, `f18d97b`.

## Preparazione asincrona dei file importati

- Spostata fuori dal costruttore della finestra la lettura dei tag musicali e l'estrazione titolo/anno dei file importati singolarmente.
- Il worker di avvio prepara ora sia le cartelle locali configurate sia i file importati, quindi consegna i risultati al thread Qt tramite il segnale già usato per la libreria.
- I file importati che appartengono già a una cartella configurata non vengono preparati una seconda volta; vengono inoltre esclusi i percorsi già presenti nella sessione.
- Il callback Qt aggiorna la sessione e i sottotitoli delle righe importate solo dopo la preparazione in background.
- Aggiunto un test dedicato al worker. La CI sul commit `b55c041` ha superato compilazione e 103 test di regressione/Qt.
- Il rendering libmpv e la verifica pratica dell'avvio restano da eseguire sul sistema Linux di prova.

Commit: `c868b66`, `9fe7995`, `7493e57`, `94586e1`, `b55c041`.


## Menu contestuali dei canali e delle guide — Qt6

- Ripristinate nel menu contestuale della lista centrale le azioni IPTV della Stable 4.4.4: rinomina del nome visualizzato, assegnazione/rimozione logo e scelta/rimozione del colore manuale.
- Per i file locali sono disponibili assegnazione/rimozione copertina; le azioni Preferiti già presenti restano disponibili.
- Il nome personalizzato viene applicato alla lista e alla barra di stato senza sostituire il nome originale usato per identificare il canale e associare l'EPG.
- Ripristinata anche la rinomina delle guide EPG dal menu contestuale della sidebar; il nome utente viene mostrato nell'albero e resta separato dal nome sorgente.
- Aggiunti dodici test Qt per menu IPTV, menu file locali, persistenza/ripristino dei nomi, colore manuale, rinomina delle guide, gestione delle copertine locali e navigazione URL.
- Commit implementazione: `ef77c63`, `8819662`. Commit test: `1e1ee10`, `6db5b0f`.
- Ripristinato il percorso copertina della Stable per i media locali: immagine accanto al file con nome base `.jpg`, conversione JPEG e priorità della copertina locale nella lista; le URL continuano a usare la cache dedicata.
- Aggiunti due test per il percorso locale/remoto e il salvataggio/lettura effettiva della copertina. Commit implementazione: `75fe379`, `8758cfa`. Commit test: `ff42e48`.
- Ripristinato l'albero URL della Stable: cartelle Podcast, Music, Radio, IP cam, Film, Video e Temporary, con selezione della categoria, apertura diretta, nomi personalizzati e menu contestuale già collegato.
- Aggiunti due test per la costruzione dell'albero URL e la navigazione tra categorie/indirizzi. Commit implementazione: `ac8321a`. Commit test: `8d737e2`.
- Corretto il ripristino del nome URL personalizzato: svuotando il campo viene eliminato l'alias e torna il titolo derivato dall'indirizzo. Test aggiunto. Commit implementazione: `f5c011c`. Commit test: `3316df3`.
- La selezione diretta di un indirizzo dalla sidebar conserva ora la categoria di provenienza (incluse le URL temporanee), così la lista centrale resta nel contesto corretto. Test di navigazione esteso. Commit implementazione: `732710b`. Commit test: `380e273`.
- Verifica CI dei nuovi commit: in attesa; nessuna prova runtime su X11/Wayland è stata eseguita.
