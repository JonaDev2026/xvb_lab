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
- [x] Aggiunti test per i casi titolo/anno, struttura cartelle musicali, poster e cache JSON.
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
