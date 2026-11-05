# XVB Lab — Diario di progetto

## 1. Scopo

Ricostruire XVB Player in un progetto indipendente, mantenendo le funzionalità e il comportamento della versione stabile **XVB 4.4.4**.

- Repository di riferimento: https://github.com/JonaDev2026/xvb
- Versione di riferimento: tag `v4.4.4`
- Nuovo repository: https://github.com/JonaDev2026/xvb_lab
- Stable resta separata e non deve essere modificata durante lo sviluppo di XVB Lab.
- Il nuovo programma non deve essere una versione ridotta o una semplice interfaccia dimostrativa: l'obiettivo è ricostruire la stessa applicazione.

Questo documento è il diario permanente del progetto. Va aggiornato quando si prendono decisioni, si completano moduli o si verificano differenze rispetto alla Stable.

## 2. Stack tecnologico deciso

Il linguaggio resta **Python**. La riscrittura riguarda soprattutto l'architettura e il framework grafico.

- **Python 3** — linguaggio principale.
- **PySide6 / Qt 6** — interfaccia grafica, finestre, menu, modelli, eventi e controlli.
- **libmpv** — motore di riproduzione.
- **libmpv Render API** — rendering video integrato nel ciclo grafico Qt, senza dipendere dalla finestra X11 tramite `wid`.
- **SQLite** — da valutare per indicizzazione e librerie grandi; non sostituisce automaticamente i file di configurazione e le cache esistenti.
- **D-Bus / MPRIS** — integrazione con tasti multimediali e desktop Linux.

### Compatibilità grafica

Obiettivo: una sola applicazione utilizzabile su **X11 e Wayland**.

La nuova implementazione non deve basarsi su:
- Tkinter;
- Xlib per incorporare il video;
- identificatori finestra X11 passati a mpv con `wid`;
- overlay che funzionano solo grazie a coordinate o finestre X11.

La superficie video deve essere gestita da Qt e dal rendering di libmpv. La scelta concreta del backend grafico (OpenGL o altro backend supportato) va verificata con un prototipo prima di costruire tutta l'interfaccia. Su Wayland devono essere usati i normali backend Qt Wayland; su X11 il backend Qt XCB.

## 3. Analisi della Stable 4.4.4

Analisi basata sul tag `v4.4.4` del repository ufficiale. Il file principale `xvb.py` contiene circa 11.823 righe e 474 KB; `traduzioni.py` contiene le traduzioni. La Stable è un'applicazione Tkinter con motore python-mpv/libmpv.

La ricostruzione dovrà quindi separare responsabilità oggi concentrate nella classe `TV` e nel file monolitico.

### 3.1 Interfaccia e organizzazione

Da conservare:
- finestra principale, tema scuro, colori, icone e proporzioni;
- menu Media, Playback, Video, Audio, IPTV, View e Settings/Information;
- area di riproduzione e controlli;
- elenco ad albero delle playlist e delle categorie;
- pannello laterale e libreria locale;
- selezione, ricerca e filtri;
- menu contestuali e operazioni sulle righe;
- barra di stato, informazioni sul contenuto in riproduzione e indicatori;
- ridimensionamento dei pannelli, fullscreen e gestione delle finestre;
- icone e risorse grafiche originali del progetto;
- lingua inglese predefinita e scelta della lingua, mantenendo le lingue già presenti.

La nuova UI deve mantenere la logica e l'usabilità della Stable. Qt non è un motivo per cambiare arbitrariamente disposizione, colori o flussi di lavoro.

### 3.2 IPTV, playlist e sorgenti

Da ricostruire:
- caricamento di playlist M3U locali e remote;
- aggiunta, rimozione, rinomina, aggiornamento e apertura delle playlist;
- categorie e sottocartelle delle playlist;
- lettura di `EXTINF`, nomi, `tvg-id`, `tvg-logo`, `group-title` e metadati supportati;
- gestione delle playlist senza estensione, riconoscendone il contenuto;
- cache delle playlist remote, aggiornamento e uso della copia locale in caso di problemi di rete;
- cache dei dati M3U analizzati, con verifica di data e dimensione;
- ricerca e filtro dei canali;
- canali preferiti, playlist preferite e categorie dei preferiti;
- canali recenti/ultimo canale e ripristino dello stato;
- loghi, immagini, colori e indicatori dei canali;
- varianti/qualità degli stream;
- supporto agli header HTTP necessari agli stream;
- gestione ClearKey e manifest DASH dove prevista dalla Stable;
- apertura diretta di URL e sorgenti temporanee o salvate.

La gerarchia e le regole di visualizzazione già presenti nella Stable vanno rilevate dal codice e mantenute, senza inventare una nuova struttura.

### 3.3 EPG e guida TV

Da ricostruire:
- caricamento di guide XMLTV locali e remote;
- più sorgenti EPG e unione delle guide;
- associazione dei programmi ai canali tramite identificativi e nomi;
- parsing e normalizzazione di date e orari XMLTV;
- ricerca dei programmi;
- guida grafica con asse temporale, righe dei canali e scorrimento;
- programma attuale e successivo;
- aggiornamento manuale e automatico delle guide;
- cache e gestione degli errori di download;
- avvio della riproduzione e delle registrazioni dai programmi della guida.

### 3.4 Registrazioni

Da ricostruire:
- registrazione immediata del flusso;
- arresto della registrazione;
- pianificazione basata su programma/orario;
- controllo dell'inizio e della fine pianificati;
- gestione delle registrazioni in corso e concluse;
- elenco, apertura e cartella delle registrazioni;
- indicazione dello stato di registrazione nell'interfaccia.

### 3.5 Libreria locale: video e musica

Da ricostruire:
- importazione e scansione di cartelle;
- separazione e navigazione tra Video e Music;
- ricerca e filtri;
- elenco dei file e ordinamento;
- riproduzione, coda, selezione e stato del file in riproduzione;
- durata, informazioni e metadati;
- lettura tag musicali tramite Mutagen;
- cache dei tag e degli artisti;
- copertine di album e immagini degli artisti;
- poster e anteprime video;
- ricerca e download metadati TMDB;
- copertine MusicBrainz e ricerca basata sui brani;
- cache persistente delle immagini e delle informazioni;
- azioni contestuali per rinominare, assegnare o rimuovere copertine;
- visualizzazione musicale con disco/vinile e animazioni già presenti;
- avanzamento/progresso e indicatori nella lista;
- gestione efficiente di librerie grandi: non bloccare l'interfaccia e non rieseguire scansioni inutili.

### 3.6 Dischi e supporti

Da ricostruire e verificare sul codice:
- rilevamento dei supporti;
- DVD video non cifrati;
- dischi dati;
- immagini ISO;
- CD audio;
- visualizzazione e identificazione dei dischi;
- titoli e metadati DVD tramite TMDB, dove disponibili;
- gestione dei supporti rimossi o non leggibili.

La Stable non promette la riproduzione di Blu-ray: non aggiungerla come funzionalità senza una decisione esplicita e una verifica tecnica.

### 3.7 Telecamere e sorgenti di rete

Da ricostruire:
- stream RTSP;
- telecamere IP;
- sorgenti ONVIF, secondo quanto effettivamente implementato nella Stable;
- categorie e salvataggio degli URL;
- apertura temporanea o memorizzata delle sorgenti;
- nome personalizzato e riproduzione;
- opzioni mpv e header specifici richiesti dalle sorgenti.

### 3.8 Funzioni del player

Da mantenere:
- play, pausa, stop, precedente e successivo;
- seek e avanzamento/riavvolgimento;
- velocità di riproduzione;
- proporzioni, adattamento e riempimento/crop;
- deinterlacciamento e decodifica hardware;
- luminosità, contrasto e saturazione;
- screenshot;
- selezione delle tracce audio e sottotitoli;
- caricamento sottotitoli locali e ricerca online tramite OpenSubtitles;
- ritardo e dimensione dei sottotitoli;
- ritardo audio;
- dispositivi di uscita audio;
- equalizzatore, boost e normalizzazione audio;
- buffer configurabile;
- ripetizione singola/tutta e shuffle;
- timer di spegnimento;
- loop A-B;
- capitoli;
- gestione dei flussi e delle varianti di qualità;
- rilevamento fine riproduzione, errori e canali non disponibili.

### 3.9 Finestre e modalità di visualizzazione

Da mantenere:
- fullscreen;
- Picture-in-Picture;
- split screen e secondo output mpv;
- selezione schermo;
- sempre in primo piano;
- barra e controlli in overlay;
- HUD e informazioni di riproduzione;
- nascondere/mostrare pannelli;
- gestione mouse e controlli che appaiono/scompaiono;
- sfondo, poster e transizioni;
- comportamento coerente su X11 e Wayland.

Le funzioni di overlay, PiP e split screen richiedono progettazione specifica in Qt: non vanno trasposte meccanicamente dalle finestre Tkinter.

### 3.10 Integrazione desktop e sistema

Da mantenere:
- MPRIS su D-Bus;
- tasti multimediali;
- titolo, artista, album e copertina esposti al desktop;
- comandi Play/Pause/Stop/Next/Previous/Seek;
- apertura file da file manager e drag & drop;
- singola istanza dell'applicazione;
- passaggio dei nuovi file/URL all'istanza già aperta tramite socket locale;
- gestione pulita della chiusura e delle risorse.

### 3.11 Configurazione, cache e dati

Da preservare:
- lingua;
- playlist e sorgenti salvate;
- EPG;
- preferiti;
- playlist e canale usati più di recente;
- cartelle importate;
- recenti;
- URL e nomi personalizzati;
- preferenze audio/video;
- buffer, velocità, ripetizione e shuffle;
- pannelli e cartelle aperte;
- tag, copertine, colori e cache;
- credenziali OpenSubtitles, conservate separatamente e con permessi restrittivi.

Percorsi e formati esistenti sotto `~/.config/xvb`, `~/.cache/xvb` e `~/.local/share/xvb` devono essere inventariati prima di decidere eventuali migrazioni. Non cancellare né sovrascrivere i dati della Stable. La nuova app deve iniziare in modo isolato, con possibilità di importare i dati in seguito.

## 4. Architettura proposta per XVB Lab

Decisione architetturale aggiornata il 2026-11-05: **il motore deve essere separato dalle funzioni dell'applicazione**, con una divisione netta e riconoscibile, analoga alla separazione già adottata per le traduzioni.

Il motore è un componente autonomo: gestisce libmpv, rendering, audio/video, comandi, eventi e stato della riproduzione. Le funzioni dell'applicazione non devono contenere codice interno del motore né dipendere direttamente dai dettagli di libmpv. Devono comunicare con il motore attraverso un'interfaccia/API interna ben definita.

Le traduzioni restano un'area autonoma, separata sia dal motore sia dalle funzioni.

### 4.1 Struttura principale

La struttura di riferimento diventa:

```
xvb_lab/
├── main.py
├── engine/
│   ├── __init__.py
│   ├── mpv.py
│   ├── render.py
│   ├── audio.py
│   ├── video.py
│   └── events.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── cache.py
│   ├── database.py
│   └── workers.py
├── ui/
│   ├── __init__.py
│   ├── window.py
│   ├── player.py
│   ├── panels.py
│   └── dialogs.py
├── features/
│   ├── iptv/
│   ├── epg/
│   ├── recordings/
│   ├── music/
│   ├── videos/
│   ├── discs/
│   ├── cameras/
│   └── subtitles/
├── integrations/
│   ├── mpris.py
│   ├── dbus.py
│   └── desktop.py
├── translations/
│   ├── __init__.py
│   ├── it.py
│   └── en.py
├── resources/
│   ├── icons/
│   ├── images/
│   └── fonts/
├── tests/
└── PROGETTO.md
```

### 4.2 Responsabilità dei componenti

- **engine/** — solo motore di riproduzione: inizializzazione e controllo di libmpv, Render API, superficie video, audio, video, eventi e stato del playback. Deve essere indipendente dalle singole funzioni IPTV, musica, video, dischi e telecamere.
- **core/** — servizi condivisi: configurazione, percorsi, cache, database e gestione dei lavori in background.
- **ui/** — componenti grafici Qt: finestra principale, player visuale, pannelli, finestre e dialoghi. Non deve contenere la logica specifica delle funzioni.
- **features/** — funzioni dell'applicazione, organizzate in moduli indipendenti. Ogni modulo usa l'interfaccia del motore quando deve riprodurre un contenuto.
- **integrations/** — collegamenti con il desktop Linux, D-Bus, MPRIS e servizi esterni al programma.
- **translations/** — traduzioni separate dal resto del codice, senza stringhe dell'interfaccia sparse nei moduli.
- **resources/** — icone, immagini, font e altre risorse.
- **tests/** — test dei componenti e delle funzioni.

### 4.3 Regole di separazione

1. Il motore non deve conoscere IPTV, EPG, musica, video, registrazioni o telecamere.
2. Le funzioni non devono pilotare direttamente oggetti o API interne di libmpv: usano l'interfaccia esposta da `engine/`.
3. L'interfaccia grafica non deve incorporare la logica delle singole funzioni.
4. Le traduzioni devono rimanere in moduli dedicati e centralizzati.
5. I componenti comunicano tramite interfacce e segnali/eventi definiti, evitando dipendenze circolari.
6. Un cambiamento al motore non deve obbligare a riscrivere le funzioni, se l'interfaccia pubblica resta invariata.
7. La struttura può essere ampliata quando necessario, ma senza accorpare nuovamente tutto in un unico file.

## 5. Regole di sviluppo

1. La Stable 4.4.4 è il riferimento funzionale; non si modifica.
2. XVB Lab è indipendente e può evolvere senza alterare Stable.
3. Prima si analizza il comportamento della funzione originale, poi la si riscrive e la si prova.
4. Una funzione non è completata solo perché esiste un pulsante: deve funzionare end-to-end.
5. Non rimuovere funzionalità per semplificare la prima versione.
6. Non cambiare arbitrariamente grafica, nomi, flussi o comportamento.
7. Le operazioni lente (rete, scansione, parsing, immagini, EPG) devono stare fuori dal thread UI; aggiornare Qt tramite segnali/slot.
8. Gli errori devono essere gestiti e registrati senza bloccare l'interfaccia.
9. Cache e scritture devono essere sicure, coerenti e non corrompere i dati.
10. Non leggere o migrare automaticamente i dati della Stable durante i primi test.
11. Ogni fase deve lasciare il programma avviabile e verificabile.
12. Prima di dichiarare supporto Wayland, provarlo realmente in una sessione Wayland; fare anche test X11.
13. Nessun intervento sul repository Stable senza richiesta esplicita.
14. Procedere una cosa alla volta e aggiornare questo diario a ogni decisione o completamento.

## 6. Piano di lavoro

### Fase 0 — Inventario e base del progetto
- [ ] Verificare il contenuto effettivo del repository `xvb_lab`.
- [ ] Creare la struttura iniziale.
- [ ] Definire dipendenze e avvio in ambiente virtuale.
- [ ] Aggiungere logging e gestione eccezioni.
- [ ] Aggiungere test di base.
- [ ] Registrare nel diario commit e decisioni iniziali.

### Fase 1 — Prototipo Qt6 + libmpv
- [ ] Finestra PySide6 minima.
- [ ] Superficie video Qt.
- [ ] Avvio/arresto libmpv.
- [ ] Riproduzione file locale e stream di rete.
- [ ] Play/Pause/Stop, volume e seek.
- [ ] Verifica rendering in X11.
- [ ] Verifica rendering nativo in Wayland.
- [ ] Verifica chiusura, riapertura e rilascio risorse.

Questa fase è il blocco tecnico più importante. Non iniziare a trasferire tutta la UI prima di avere un rendering affidabile su entrambi i sistemi.

### Fase 2 — Finestra principale e player
- [ ] Tema, icone, layout e controlli.
- [ ] Menu principali.
- [ ] Barra di stato e informazioni sul contenuto.
- [ ] Fullscreen e controlli overlay.
- [ ] Preferenze e configurazione.
- [ ] Lingue e traduzioni.

### Fase 3 — Playlist e IPTV
- [ ] Parser M3U e cache.
- [ ] Albero playlist/categorie.
- [ ] Ricerca e filtri.
- [ ] Loghi, preferiti e recenti.
- [ ] Varianti qualità e header.
- [ ] ClearKey/DASH secondo compatibilità verificata.
- [ ] Apertura URL e sorgenti salvate.

### Fase 4 — EPG e registrazioni
- [ ] Parser XMLTV.
- [ ] Unione guide e associazione canali.
- [ ] Finestra guida.
- [ ] Programmi attuali/successivi.
- [ ] Registrazione immediata.
- [ ] Programmazione e gestione registrazioni.

### Fase 5 — Libreria locale
- [ ] Scansione cartelle.
- [ ] Video e musica.
- [ ] Mutagen e cache tag.
- [ ] TMDB e MusicBrainz.
- [ ] Poster, copertine e foto artisti.
- [ ] Ricerca, ordinamento e menu contestuali.
- [ ] Prestazioni con librerie grandi.

### Fase 6 — Dischi, telecamere e funzioni avanzate
- [ ] DVD non cifrati, dischi dati, ISO e CD audio.
- [ ] RTSP e ONVIF.
- [ ] Sottotitoli locali e OpenSubtitles.
- [ ] Tracce, capitoli, audio e filtri video.
- [ ] Equalizzatore, normalizzazione e dispositivi audio.
- [ ] Buffer, loop A-B, timer, shuffle e repeat.
- [ ] PiP, split screen, selezione schermo e HUD.

### Fase 7 — Integrazione desktop e robustezza
- [ ] MPRIS e tasti multimediali.
- [ ] Drag & drop e apertura da file manager.
- [ ] Singola istanza e socket locale.
- [ ] Test di stabilità, prestazioni e recupero errori.
- [ ] Test X11 e Wayland su sessioni reali.

### Fase 8 — Distribuzione
- [ ] Avvio desktop e icone.
- [ ] Pacchetto Debian.
- [ ] Dipendenze e risorse.
- [ ] Documentazione e README.
- [ ] Test installazione, aggiornamento e disinstallazione.

## 7. Criteri di completamento

XVB Lab potrà essere considerata equivalente alla Stable solo quando:
- tutte le funzioni della 4.4.4 sono state inventariate e implementate oppure una differenza è stata approvata esplicitamente;
- i flussi principali sono testati con file locali, playlist M3U, EPG e stream;
- la libreria locale funziona anche con raccolte grandi;
- registrazione, sottotitoli, audio, DVD e telecamere sono verificati;
- MPRIS e apertura da desktop funzionano;
- la riproduzione video è verificata su X11 e Wayland;
- non vengono persi o alterati i dati della Stable.

## 8. Stato attuale

**La base applicativa Qt6 è presente nel branch `main`, ma non è ancora dichiarata equivalente alla Stable 4.4.4 e non è ancora la build da collaudare.**

### Componenti presenti

- [x] Repository Stable di riferimento: `JonaDev2026/xvb`, tag `v4.4.4`.
- [x] Inventario della Stable: 8 classi, 400 metodi e 106 funzioni top-level.
- [x] Traduzioni originali trasferite in `i18n/`.
- [x] Servizi condivisi trasferiti in `core/`: configurazione, media, playlist, EPG, preferiti, metadati, tag, colori, artwork, dischi, anteprime, registrazioni, stream e rilevamento font.
- [x] Motore libmpv con Qt Render API in `engine/mpv.py`, superficie OpenGL Qt, comandi, proprietà ed eventi.
- [x] Integrazione MPRIS in `integrations/mpris.py`.
- [x] Finestra applicativa in `ui/main_window.py`, avvio da `main.py`.
- [x] Widget UI suddivisi in moduli: `ui/search.py`, `ui/dialogs.py`, `ui/list.py`, `ui/guide.py`.
- [x] Albero laterale Qt6 in `ui/sidebar.py`, collegato alle playlist, categorie, libreria locale, dischi, registrazioni e preferiti.
- [x] Controlli player, seek, volume, repeat, shuffle, preferiti, fullscreen, PiP e split screen collegati alle funzioni presenti nel controller.
- [x] Test di regressione presenti in `tests/` e workflow CI configurato.
- [x] Aggiornamento automatico delle guide EPG ripristinato: controllo ogni 30 minuti, cache remota di sei ore e rilevamento delle modifiche ai file locali, con test CI superati.
- [x] Albero Registrazioni collegato alla lista centrale per gruppo canale/data; durata dei file locali calcolata in background per le barre di avanzamento. Test Qt e CI superati.
- [x] MPRIS aggiornato ogni secondo con metadati locali, programma EPG e copertine/loghi; timer gestito in apertura e chiusura. Test Qt e CI superati.
- [x] Avvio a istanza singola con inoltro file tramite socket Unix; apertura iniziale di playlist M3U, file e cartelle da riga di comando. Test CI superati.
- [x] File e playlist inoltrati da istanze successive selezionano/aprono il contenuto e riportano la finestra in primo piano; URL temporanee e copertine vengono ripulite alla chiusura.
- [x] Corretto l'ordine di inizializzazione dello stato in `MainWindow`; compilazione e suite di test Qt/regressione superate dalla CI sul commit `05268c1`.

### Lavoro ancora aperto

- [ ] Confronto puntuale di ogni metodo trasferito con il corpo della Stable, non solo con l'inventario.
- [ ] Migrazione completa dei metodi rimanenti della classe `TV`.
- [ ] Parità completa di menu, menu contestuali, barra overlay, HUD, finestre e scorciatoie.
- [ ] Verifica di tutti i flussi end-to-end: IPTV, EPG, registrazioni, musica, video, dischi, CD, telecamere e sottotitoli.
- [ ] Verifica del rendering e della stabilità libmpv in sessioni X11 e Wayland reali.
- [ ] Esecuzione dei test e collaudo completo.

Le modifiche di questa fase non sono state collaudate localmente. Il pull verrà richiesto quando la prima build completa sarà pronta per una prova complessiva.
