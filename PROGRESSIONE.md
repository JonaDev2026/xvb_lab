# XVB Lab — Registro di progressione

Questo documento registra in ordine cronologico il lavoro effettivamente svolto su XVB Lab. È il registro operativo: non sostituisce `PROGETTO.md`, che resta il riferimento per obiettivi, architettura, inventario delle funzioni e piano generale.

## Regole del registro

1. Registrare ogni passaggio significativo, prima di iniziare il successivo.
2. Per ogni modifica indicare data, file coinvolti, cosa è cambiato e perché.
3. Riportare il commit Git quando disponibile.
4. Distinguere sempre tra codice scritto, codice verificato e funzione realmente collaudata.
5. Non segnare come funzionante una parte che non è stata eseguita e provata.
6. Annotare errori, risultati dei test, correzioni e questioni ancora aperte.
7. Aggiornare questo file nello stesso intervento in cui si aggiornano i sorgenti.
8. Non modificare la Stable `JonaDev2026/xvb`: il lavoro riguarda esclusivamente `JonaDev2026/xvb_lab`.

## Stato sintetico

- **Progetto:** ricostruzione di XVB Player Stable 4.4.4.
- **Repository:** https://github.com/JonaDev2026/xvb_lab
- **Branch di lavoro:** `main`
- **Riferimento funzionale:** https://github.com/JonaDev2026/xvb/tree/v4.4.4
- **Architettura:** Python, PySide6/Qt6, libmpv Render API; motore separato dalle funzioni.
- **Ultimo commit noto:** `ff4d16472974e820b92bcce75f923ac8b1dff128` (azioni contestuali Local)
- **Stato tecnico:** base Qt e primo collegamento Qt/libmpv presenti nel repository; esecuzione e rendering non ancora verificati sul computer di sviluppo.
- **Funzioni della Stable trasferite:** nessuna funzione completa risulta ancora trasferita e collaudata.

## Come registrare i prossimi interventi

Usare questo schema per ogni nuova voce:

```markdown
### AAAA-MM-GG — Titolo del passaggio

**Obiettivo**
Descrizione del risultato che si vuole ottenere.

**File creati o modificati**
- `percorso/file.py` — descrizione precisa.

**Modifiche**
- Elenco delle modifiche effettivamente applicate.

**Verifica**
- Comando o procedura eseguita.
- Risultato osservato.
- Distinguere test superati, falliti e non eseguiti.

**Commit**
- SHA e messaggio, se disponibile.

**Stato e prossimo passaggio**
- Cosa è concluso.
- Cosa resta da fare, senza anticipare attività non ancora eseguite.
```

---

## Cronologia

### 2026-11-05 — Creazione del registro di progressione

**Obiettivo**

Aggiungere un registro operativo cronologico separato dal diario generale, per conservare la sequenza precisa di passaggi e modifiche e facilitare la ripresa del lavoro tra sessioni.

**File creati o modificati**

- `PROGRESSIONE.md` — nuovo registro operativo.

**Modifiche**

- Definita la distinzione tra diario di progetto e registro di progressione.
- Inserite le regole per annotare ogni modifica e il relativo stato di verifica.
- Registrata la situazione tecnica nota fino a questo momento.
- Riportati i commit già noti e i file coinvolti nei passaggi precedenti.

**Verifica**

- Contenuto preparato sulla base della cronologia Git e delle informazioni registrate in `PROGETTO.md`.
- Il prototipo Qt/libmpv non è stato ancora collaudato sul computer di sviluppo.

**Commit**

- Da assegnare alla creazione di questo file.

**Stato e prossimo passaggio**

- Il registro operativo è stato preparato.
- Prima di proseguire con nuove modifiche al codice, sincronizzare il clone locale e verificare il prototipo già presente nel repository.

### 2026-11-05 — Primo collegamento Qt/libmpv

**Obiettivo**

Preparare il rendering video integrato nella UI Qt senza utilizzare l'embedding X11 tramite `wid`.

**File creati o modificati**

- `engine/render.py` — nuovo widget Qt basato su `QOpenGLWidget` e libmpv Render API.
- `engine/mpv.py` — aggiornamento del controller libmpv.
- `main.py` — collegamento della finestra Qt al widget video e ai comandi minimi.

**Modifiche**

- Implementato il primo tentativo di creazione del render context OpenGL di libmpv.
- Collegato il framebuffer del widget Qt alla chiamata di rendering di libmpv.
- Aggiunta la callback di aggiornamento del frame.
- Impostato `vo=libmpv` nel motore.
- Collegati i comandi minimi di apertura file e stop.

**Commit**

- `engine/render.py`: `1cca9d8516a7a661ea92634ad72aa2823e762126`
- `engine/mpv.py`: `419f903ccaa53719badc7ccf5afd160a19e6a89f`
- `main.py`: `057c187575026689adfb601a1532446889f24d81`
- Aggiornamento del diario e dell'architettura: `4d0d69b1341aec8b2648fccb168ff04b8c71d9c9`

**Verifica**

- Implementazione presente nel repository.
- Non risultano ancora prove di esecuzione sul computer di sviluppo.
- Da verificare recupero dei puntatori OpenGL da Qt, creazione del render context, visualizzazione del video, orientamento del frame, callback e rilascio delle risorse.
- Compatibilità X11 e Wayland ancora da verificare separatamente.

**Stato e prossimo passaggio**

- Codice iniziale scritto, non ancora collaudato.
- Il primo controllo deve essere eseguito dopo il pull del repository locale. Non considerare il rendering funzionante fino alla prova effettiva.

### 2026-11-05 — Avvio della base tecnica

**Obiettivo**

Creare lo scheletro iniziale del nuovo progetto e un primo controller libmpv autonomo.

**File creati o modificati**

- `requirements.txt` — dipendenza iniziale PySide6.
- `main.py` — prima finestra Qt minimale.
- `engine/__init__.py`
- `engine/mpv.py` — primo controller libmpv tramite API C.
- Package iniziali: `core/`, `ui/`, `features/`, `integrations/`, `translations/`, `tests/`.

**Modifiche**

- Avviata la struttura modulare del repository.
- Separato il primo controller libmpv dal codice della finestra.
- Evitati Tkinter, Xlib e il parametro finestra `wid` nel controller.

**Verifica**

- File creati e versionati.
- Non risulta ancora un test di esecuzione sul computer di sviluppo.

**Stato e prossimo passaggio**

- Base iniziale presente.
- Il controller e la finestra devono essere verificati nell'ambiente reale prima di aggiungere altre funzioni.

### 2026-11-05 — Decisione di separare motore e funzioni

**Obiettivo**

Definire confini architetturali chiari per evitare che il nuovo progetto torni a essere un'applicazione monolitica.

**Decisioni**

- `engine/` contiene esclusivamente il motore di riproduzione e la sua API.
- `features/` contiene le funzioni applicative: IPTV, EPG, registrazioni, musica, video, dischi, telecamere e sottotitoli.
- `ui/` contiene i componenti grafici.
- `core/` contiene i servizi condivisi.
- `integrations/` contiene le integrazioni con il desktop.
- `translations/` resta separata e centralizzata.
- Le funzioni comunicano con il motore attraverso un'interfaccia interna stabile e non accedono direttamente ai dettagli di libmpv.

**File aggiornati**

- `PROGETTO.md` — struttura e regole architetturali.

**Commit**

- `4d0d69b1341aec8b2648fccb168ff04b8c71d9c9`

**Stato**

- Decisione architetturale registrata. L'implementazione completa dei moduli è ancora da realizzare.

### 2026-11-05 — Definizione del progetto

**Obiettivo**

Ricostruire XVB Player mantenendo le funzionalità della Stable 4.4.4 e adottando una nuova base grafica compatibile con X11 e Wayland.

**Decisioni iniziali**

- Repository nuovo e indipendente: `JonaDev2026/xvb_lab`.
- Riferimento funzionale: Stable `v4.4.4` nel repository `JonaDev2026/xvb`.
- Stack scelto: Python, PySide6/Qt6 e libmpv.
- La Stable non deve essere modificata.
- La ricostruzione deve mantenere le funzioni originali, non ridursi a un player dimostrativo.

**Analisi registrata**

- Analizzato il sorgente principale `xvb.py` della Stable 4.4.4.
- Individuate le principali aree funzionali e le risorse/traduzioni.
- Preparato `PROGETTO.md` come diario generale e specifica di riferimento.

**Stato**

- Obiettivo e riferimento funzionale definiti.
- Nessuna funzione della Stable ancora trasferita.


### 2026-11-05 — Prima ricostruzione della finestra principale Qt

**Obiettivo**

Sostituire la finestra dimostrativa con la prima struttura grafica ricavata direttamente dalla Stable 4.4.4, mantenendo il widget video libmpv già verificato.

**File creati o modificati**

- `ui/main_window.py` — nuova finestra principale Qt.
- `main.py` — avvio dell'applicazione collegato alla nuova finestra e caricamento facoltativo del font Google Sans e dell'icona originali.

**Modifiche**

- Impostate le dimensioni iniziali originali 1280 × 720 e il titolo XVB v4.4.4.
- Ricostruiti i pannelli sinistro, video centrale e destro con splitter ridimensionabile e dimensioni iniziali 300/760/220.
- Aggiunti ricerca, albero media, pannello Playlists e albero delle playlist.
- Ricostruiti i sette menu principali: Media, Playback, Video, Audio, IPTV, View e Help, con le voci rilevate nel sorgente Stable.
- Aggiunta la barra comandi da 96 px con le icone originali disponibili, i controlli di riproduzione già collegabili al motore e il cursore volume.
- Aggiunta la barra di stato da 28 px con campi predisposti per categoria, playback, titolo, guida, formato e orologio locale.
- Aggiunta la barra notifiche da 42 px, inizialmente nascosta.
- Mantenuti i colori principali rilevati nel sorgente Stable.
- Le voci non ancora trasferite sono disabilitate: la presenza grafica di una voce non viene considerata implementazione della relativa funzione.
- La gerarchia dei menu è stata rifinita per corrispondere alla disposizione originale delle voci e delle intestazioni.

**Verifica**

- Codice scritto e pubblicato nel repository.
- Non ancora eseguito sul computer di sviluppo dopo queste modifiche.
- Da verificare import Qt, layout effettivo, caricamento delle icone, dimensioni, ridimensionamento dei pannelli e collegamento dei comandi.
- Le funzioni IPTV, EPG, libreria, registrazioni, PiP, split screen, MPRIS e le altre voci disabilitate restano da implementare.

**Commit**

- `61e5297c95818882ad4f59603796b37973729665` — creazione della finestra.
- `532eb5ccaaed5b2f35c640d58110531bb29a4b38` — orologio localizzato.
- `a41c054b60e8d8f1b6e348f8a08f1ddc54c1d022` — collegamento di main.py.
- `f1792f771960089868bf8fbc664306bef553a29c` — regolazione pannelli e barra comandi.

**Stato e prossimo passaggio**

- Prima struttura grafica scritta, non ancora collaudata.
- La finestra non è ancora equivalente alla Stable: i contenuti degli alberi, le interazioni, i menu e le funzioni applicative devono essere trasferiti e verificati.

### 2026-11-05 — Primo trasferimento della libreria locale

**Obiettivo**

Trasferire in XVB Lab il primo flusso reale della sezione Local della Stable 4.4.4: aggiunta di cartelle, scansione dei contenuti, visualizzazione dei file e avvio della riproduzione.

**File creati o modificati**

- `core/config.py` — configurazione persistente isolata in `~/.config/xvb-lab/config.json`.
- `features/local_media.py` — riconoscimento dei formati audio/video e scansione ricorsiva delle cartelle.
- `ui/main_window.py` — collegamento di Open folder, albero Local, sorgenti importate, ricerca e doppio clic per riprodurre.

**Modifiche**

- Aggiunto un archivio di configurazione indipendente: non legge, modifica o sovrascrive la configurazione della Stable.
- Aggiunta l'importazione di cartelle locali e il salvataggio persistente dei percorsi.
- La scansione ricorsiva ignora le directory e i file nascosti e ordina i risultati senza distinzione tra maiuscole e minuscole.
- La scansione viene eseguita in un thread Qt separato per non bloccare la finestra.
- I risultati sono mostrati nell'elenco sinistro; il doppio clic invia il percorso al motore libmpv.
- Open file registra il file nella sezione Imported e avvia la riproduzione.
- Aggiunto il filtro testuale sulla lista caricata.

**Verifica**

- Modifiche pubblicate su GitHub.
- Non ancora eseguite né collaudate sul computer di sviluppo dopo questo aggiornamento.
- Da verificare: compilazione Python, apertura cartella, scansione di una libreria ampia, filtro, riproduzione e chiusura durante una scansione.
- La struttura completa della libreria Stable (sottocategorie, conteggi, poster, metadati, cache e azioni contestuali) non è ancora trasferita.

**Commit**

- `ca551d9d5d0e65233ac1e9e749ca385df3b272b4` — configurazione isolata.
- `6cd0dff27ab7712afb09a60b7b1e52ec2be1d446` — servizio scansione media.
- `2747a8ba396f084188f185c1f165d24e3459aa03` — collegamento UI della libreria locale.

**Stato e prossimo passaggio**

- Primo flusso della libreria locale scritto, non ancora collaudato.
- Proseguire trasferendo la gerarchia e le interazioni dell'albero laterale della Stable, poi completare la libreria e le sue funzioni.


### 2026-11-05 — Gerarchia della libreria Local

**Obiettivo**

Avvicinare l'albero Local alla struttura della Stable 4.4.4, mantenendo la configurazione autonoma di Lab.

**Modifiche**

- Le cartelle importate vengono mostrate con il conteggio dei file audio/video trovati nella scansione.
- Le sottocartelle immediate che contengono media vengono aggiunte come nodi figli, con conteggio e icona coerente con il contenuto prevalente.
- La selezione di una sottocartella avvia la scansione della sola sottocartella.
- La sezione Imported media mostra i singoli file come nodi selezionabili, oltre al nodo complessivo.
- I percorsi continuano a essere salvati esclusivamente nella configurazione di XVB Lab.

**Verifica**

- Modifica pubblicata su GitHub.
- Non ancora compilata o provata localmente dopo questo commit.
- I conteggi e i nodi delle sottocartelle vengono aggiornati quando la cartella principale viene selezionata e completata la scansione.
- Restano da trasferire le immagini vinile originali, la cache persistente, i metadati, le azioni contestuali e il resto delle interazioni della Stable.

**Commit**

- UI: `ea322f9115d52bbee5a5cfc055dc3b21dc263036`
- Verifica locale: in attesa del pull e del collaudo sul computer di sviluppo.


### 2026-11-05 — Azioni contestuali della libreria Local

**Modifiche**

- Aggiunto il menu contestuale nell'albero Local.
- Le cartelle importate possono essere rimosse dall'elenco con richiesta di conferma.
- I singoli file importati possono essere rimossi dall'elenco senza cancellarli dal disco.
- È possibile rimuovere in un'unica operazione l'elenco Imported media, sempre senza toccare i file originali.
- La configurazione Lab viene aggiornata dopo la conferma.
- Le scansioni in background ora restituiscono anche la propria sorgente; i risultati di una scansione precedente vengono ignorati se nel frattempo è stata selezionata un'altra sorgente. Questo evita che una scansione lenta sovrascriva la lista appena selezionata.

**Verifica**

- Codice pubblicato su GitHub.
- Non ancora compilato o provato localmente dopo questo aggiornamento.
- Da collaudare: menu contestuale, conferme, persistenza dopo riavvio e scansioni consecutive.
- La rimozione riguarda esclusivamente l'elenco di XVB Lab: nessun file o cartella multimediale viene cancellato dal disco.

**Commit**

- UI: `ff4d16472974e820b92bcce75f923ac8b1dff128`
- Test locale: in attesa del pull e della verifica sul computer di sviluppo.


### 2026-11-05 — Scansione progressiva della libreria Local

**Modifiche**

- La scansione delle cartelle ora produce blocchi di 30 elementi invece di attendere il completamento dell'intera scansione.
- XVB Lab aggiunge i risultati all'elenco sinistro mentre la scansione è ancora in corso.
- La stessa modalità a blocchi viene usata per i file importati.
- Ogni scansione possiede un token progressivo: anche una nuova scansione della stessa sorgente invalida i risultati della precedente.
- Il completamento aggiorna conteggi e sottocartelle senza ricreare l'elenco già mostrato progressivamente.

**Verifica**

- Modifiche pubblicate su GitHub.
- Non ancora compilate o provate localmente dopo questo aggiornamento.
- Da verificare la visualizzazione progressiva, la selezione rapida di sorgenti diverse e la stabilità con librerie numerose.

**Commit**

- Servizio scansione: `c4de7c097c6d0ade3839ef42c250d6d2174bd7a2`
- UI: `fb12f0fe2619bde254d6d7eafa927d23a3bbc5c3`
- Aggiornamento progressione in corso.


### 2026-11-05 — Coerenza di ricerca e rimozione durante la scansione

**Modifiche**

- I nuovi risultati aggiunti progressivamente rispettano subito il filtro di ricerca già digitato.
- Rimuovere una cartella o una sorgente importata invalida anche la scansione in corso, impedendo a risultati tardivi di ripopolare la lista.
- L'avvio di una nuova scansione nasconde eventuali notifiche di errore precedenti.

**Verifica**

- Modifica pubblicata su GitHub.
- Non ancora compilata o provata localmente dopo questo aggiornamento.
- Da verificare con una ricerca avviata prima e durante una scansione e con la rimozione di una sorgente mentre è in caricamento.

**Commit**

- UI: `95f9dc69cb11033ed137763f395d334e1e9ca9a8`

### 2026-11-05 — Associazione stabile delle sorgenti nell'albero Local

**Modifiche**

- Registrato il riferimento UI di ogni sorgente Imported media, sia del nodo complessivo sia dei singoli file.
- Il completamento della scansione aggiorna il nodo Imported corretto senza dipendere dall'elemento attualmente selezionato nell'albero.
- Registrate anche le sottocartelle create dopo la scansione, così possono essere selezionate e scandite ricorsivamente.
- Quando una cartella viene aggiornata, vengono rimossi dalla mappa i riferimenti alle vecchie sottocartelle prima di ricreare i nodi.

**Verifica**

- Codice aggiornato nel repository.
- Compilazione e prova funzionale locali non ancora eseguite per questo intervento.

**Stato**

- Correzione scritta; da compilare e collaudare dopo il pull.

### 2026-11-05 — Evidenziazione della sorgente Local attiva

**Modifiche**

- Trasferita nella barra laterale l'evidenziazione della sorgente attualmente aperta, equivalente al tag `usata` della Stable.
- L'evidenziazione viene applicata alla cartella, sottocartella o nodo Imported selezionato per la scansione.
- Quando cambia sorgente, la precedente evidenziazione viene rimossa e resta evidenziato soltanto il nodo attivo.

**Verifica**

- Codice pubblicato nel repository.
- Compilazione e verifica grafica locali ancora da eseguire.

**Stato**

- Implementazione scritta; da verificare dopo il pull.


### 2026-11-05 — Icone musicali della libreria Local

**Modifiche**

- L'icona della cartella principale riflette il tipo prevalente dei contenuti: musica oppure video.
- Quando la cartella principale contiene prevalentemente musica, le sottocartelle immediate usano icone vinile.
- Il colore del vinile deriva dal nome della sottocartella con lo stesso algoritmo MD5 della Stable, quindi resta stabile tra le aperture.
- Negli altri casi le sottocartelle mantengono l'icona musica/video in base al proprio contenuto.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e verifica grafica locali ancora da eseguire.
- Da verificare dimensione e resa delle icone nella barra laterale Qt.

**Commit**

- UI: `1904ede61b26421bed1286e48c42c06ea70be694`
- Rifinitura geometria icone: `935732a7c9d1ac20c277fa94fde6056a913edc70`


### 2026-11-05 — Stato espanso delle cartelle Local

**Modifiche**

- Lo stato aperto/chiuso del nodo Local viene salvato nella configurazione Lab.
- Lo stesso comportamento è applicato alle cartelle importate, alle sottocartelle e al nodo Imported media.
- Alla ricostruzione dell'albero vengono ripristinati gli stati memorizzati.
- Le modifiche dello stato vengono salvate senza cancellare le altre impostazioni.
- La ricostruzione dell'albero blocca temporaneamente i segnali per evitare salvataggi causati dal ripristino stesso.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e verifica funzionale locali ancora da eseguire.
- Da verificare apertura/chiusura, riavvio e aggiornamento delle sottocartelle dopo una scansione.

**Commit**

- UI: `c0e69d0a73c31f9d3743bf6241c078b7b5640e61`
- Correzione ripristino Imported media: `36e37ff671fef9aeaa823795f6257a433f05d984`


### 2026-11-05 — Arresto sicuro delle scansioni Local

**Modifiche**

- Quando si seleziona una nuova sorgente, le scansioni precedenti ricevono una richiesta di interruzione.
- Il worker controlla la richiesta tra un blocco e il successivo e interrompe il lavoro non più necessario.
- Durante la chiusura della finestra vengono interrotte le scansioni attive.
- La finestra attende la conclusione dei worker; se una scansione è ancora attiva, rimanda la chiusura e riprova.
- I risultati tardivi non modificano più l'interfaccia durante la chiusura.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e prova di chiusura durante una scansione ancora da eseguire localmente.

**Commit**

- UI e worker: `c4674ffb49d334da4ce56c3eefced664f9359796`


### 2026-11-05 — Metadati musicali nella libreria Local

**Modifiche**

- Aggiunta la lettura facoltativa dei tag audio tramite Mutagen: titolo, artista, album e anno.
- Cache persistente in `~/.cache/xvb-lab/tags.json`, verificata tramite data di modifica del file.
- La lettura dei tag avviene in un worker separato, senza bloccare l'interfaccia.
- Le righe musicali mostrano titolo e sottotitolo con artista, album e anno; la ricerca viene riapplicata anche ai dati aggiornati.
- Dopo la lettura dei tag, la lista viene ordinata per titolo.
- Le scansioni dei metadati vengono interrotte quando si cambia sorgente o si chiude l'applicazione.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e verifica visiva ancora da eseguire localmente.
- Mutagen resta facoltativo: senza il pacchetto, la libreria continua a mostrare i nomi dei file.

**Commit**

- Cache tag: `c2d317c136a546aecbcc87993ff8a5ffce64e657`
- Visualizzazione: `6264f52113b08f508e10172904a1679cbde5687e`
- Correzione righe e ricerca: `7e1e492001f5d61f95186bf139f1b11fe57b80c3`


### 2026-11-05 — Copertine musicali nella libreria Local

**Modifiche**

- Le copertine incorporate nei file audio vengono estratte tramite Mutagen.
- Vengono riconosciute anche le immagini `cover`, `folder` e quelle con lo stesso nome del brano.
- Le immagini vengono memorizzate in `~/.cache/xvb-lab/covers` per evitare estrazioni ripetute.
- Le copertine vengono caricate nell'interfaccia Qt dopo il completamento del worker, senza creare QPixmap nel thread di scansione.
- Se non è disponibile una copertina, resta l'icona musicale esistente.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e controllo visivo ancora da eseguire localmente.

**Commit**

- Cache copertine: `ea76d57599796bfb1600a31207709524c77b2d65`
- Visualizzazione copertine: `f18d862467b29acb3092e5140aff0c947d74bf6e`

## Copertine manuali dei file locali

- Aggiunto al menu contestuale dei brani il comando `Set cover...` per associare un'immagine scelta dall'utente al singolo file.
- Aggiunto `Remove cover` quando è presente una copertina personalizzata.
- Le immagini personalizzate del singolo brano hanno priorità sulle copertine generiche della cartella.
- Dopo la modifica, l'icona della traccia viene aggiornata senza una nuova scansione completa.
- Modifiche scritte su GitHub; compilazione e comportamento grafico non ancora verificati localmente.


### 2026-11-05 — Navigazione Previous/Next nella libreria Local

**Modifiche**

- I pulsanti Previous e Next ora navigano tra i file visibili nella lista Local.
- La navigazione segue l'ordinamento corrente e rispetta il filtro di ricerca.
- I pulsanti si abilitano o disabilitano in base alla posizione del brano corrente.
- Il cambio di sorgente azzera il riferimento alla posizione precedente, evitando di navigare nella coda della cartella appena lasciata.
- La navigazione non modifica i file originali e non attiva ancora la riproduzione automatica a fine traccia.

**Verifica**

- Modifica pubblicata su GitHub.
- Compilazione e prova locale ancora da eseguire.


### 2026-11-05 — Apertura URL, file recenti e scorciatoie

**Modifiche**

- Attivata la voce Media → Open URL per inviare indirizzi al motore libmpv.
- Aggiunto l'elenco Recent con gli ultimi 12 file locali aperti, salvato nella configurazione Lab.
- Aggiunta la possibilità di riaprire un file recente e di svuotare l'elenco.
- Attivate scorciatoie per riproduzione/pausa, stop, navigazione precedente/successiva, ricerca temporale e schermo intero.
- Stop azzera anche il riferimento al file corrente nella navigazione locale.

**Verifica**

- Modifiche pubblicate su GitHub.
- Compilazione e prova locale ancora da eseguire.


### 2026-11-05 — Volume e mute persistenti

**Modifiche**

- Il volume viene ripristinato dalla configurazione all'avvio.
- Il valore scelto viene salvato quando si rilascia il cursore, evitando scritture continue durante il trascinamento.
- Lo stato mute viene ripristinato all'avvio e salvato a ogni cambio.
- L'icona e il suggerimento del pulsante mute si aggiornano tra Mute e Unmute.
- Le proprietà vengono applicate direttamente a libmpv.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e verifica audio locale ancora da eseguire.


### 2026-11-05 — Sincronizzazione file importati e navigazione

- L'apertura diretta di un file tramite Media → Open file ora registra il file corrente nella navigazione Local.
- Previous/Next può quindi operare anche dopo l'apertura diretta di un file importato, se presente nella lista visibile.
- Modifica pubblicata su GitHub; compilazione e verifica locale ancora da eseguire.


### 2026-11-05 — Shuffle, repeat e avanzamento automatico

**Modifiche**

- Attivata la modalità Shuffle nel menu Playback: mescola i file della lista Local e mantiene il brano corrente in cima.
- Disattivando Shuffle viene ripristinato l'ordine precedente della libreria.
- La preferenza Shuffle viene salvata nella configurazione e ripristinata all'avvio e al caricamento di una sorgente.
- Attivate le tre modalità No repeat, Repeat one e Repeat all, con selezione esclusiva e salvataggio persistente.
- Estesa l'interfaccia libmpv con la lettura della proprietà eof-reached.
- Un controllo periodico rileva la fine della riproduzione: ripete il file corrente, passa al successivo con ritorno all'inizio della lista oppure conclude la riproduzione in base alla modalità scelta.
- Il controllo ignora lo stato EOF precedente durante il caricamento di un nuovo file.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e prove funzionali locali ancora da eseguire.
- Da verificare in particolare il rilevamento EOF di libmpv, le tre modalità repeat, lo shuffle con filtri attivi e il ripristino dell'ordine.


### 2026-11-05 — Controlli di riproduzione visibili

**Modifiche**

- Portati nella barra inferiore i controlli Shuffle e Repeat, collegati alle stesse impostazioni del menu Playback.
- Il pulsante Repeat cicla tra No repeat, Repeat all e Repeat one; il tooltip mostra la modalità attiva.
- Shuffle è un pulsante selezionabile con stato visivo e tooltip aggiornato.
- Aggiunta la barra di avanzamento con posizione e durata formattate; trascinando il cursore si effettua la ricerca temporale nel file.
- Aggiunta a libmpv la lettura delle proprietà numeriche time-pos e duration.
- Play/Pause aggiorna icona e tooltip in base allo stato pause del motore.
- La barra aggiorna posizione e stato ogni mezzo secondo.

**Verifica**

- Codice pubblicato su GitHub.
- Compilazione e controllo visivo/funzionale sul sistema locale ancora da eseguire.


### 2026-11-05 — Ripristino delle metriche grafiche Stable 4.4.4

**Obiettivo**

Allineare le dimensioni fondamentali dell'interfaccia Qt ai valori effettivi della Stable, evitando misure inventate o approssimative.

**File creati o modificati**

- `ui/metrics.py` — costanti centralizzate per dimensioni e misure dell'interfaccia.
- `ui/main_window.py` — applicazione delle metriche ai pannelli, alle righe elenco, alle barre e allo stato.

**Modifiche**

- Finestra iniziale 1280×720.
- Pannello sinistro minimo 300 px e destro minimo 220 px.
- Loghi della lista media 72×56 px e righe da 64 px, come nella Stable (`LOGO_L`, `LOGO_A`, `RIGA_ELENCO`).
- Righe della sidebar playlist da 32 px, coerenti con `PUNTO + 8` della Stable.
- Barra comandi 96 px, notifica 42 px e barra di stato 28 px.
- Testo della barra di stato a 12 px.
- Le misure sono ora in un modulo UI dedicato e non sparse nella finestra.

**Verifica**

- Modifiche applicate al repository GitHub.
- Compilazione e resa grafica non ancora verificate sul computer locale.

**Commit**

- `d9ab6a78e01ac261418d76e6b6e552c09bd305e5` — modulo metriche.
- `3aacf8de0587bedda1d52aaffcc8397f51dce15e` — applicazione metriche.

**Stato e prossimo passaggio**

- Metriche principali allineate ai valori Stable.
- Restano da trasferire fedelmente struttura, componenti e comportamento dei due alberi e della barra di riproduzione.


### 2026-11-05 — Allineamento della barra comandi alla Stable

**Obiettivo**

Correggere ulteriori differenze visibili nella barra comandi, confrontandola con la disposizione effettiva della Stable 4.4.4.

**File modificati**

- `ui/main_window.py` — dimensione icone e visibilità dei controlli.

**Modifiche**

- Icone dei comandi principali riportate a 34×34 px; Stop resta 24×24 px.
- Nascosti i pulsanti Favorite e Quality, che nella Stable sono inizialmente nascosti.
- Conservati il pulsante PiP, il selettore volume e il pulsante Playlists nella barra.

**Verifica**

- Modifica registrata su GitHub.
- Avvio, compilazione e confronto visivo locale ancora da eseguire.

**Commit**

- `fa92078c74b12b4d701927cc7522ae07b3b25cf1`.

**Stato e prossimo passaggio**

- Ulteriori differenze della barra comandi corrette.
- La ricostruzione della UI non è completa: restano da trasferire struttura e contenuti reali dell'elenco media e della sidebar IPTV/EPG/M3U.
