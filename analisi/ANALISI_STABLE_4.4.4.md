# Analisi sorgente — XVB Stable 4.4.4

Sorgente analizzato direttamente dal tag `v4.4.4` del repository `JonaDev2026/xvb`.

- `xvb.py`: 11.823 righe, 474.157 caratteri.
- Classi top-level: 8 (`_XVBFiltroSicurezza`, `Ricerca`, `Cursore`, `Guida`, `Tendina`, `Elenco`, `Finestrella`, `TV`).
- La classe applicativa principale è `TV`, dichiarata alla riga 3530.
- Metodi diretti rilevati nelle 8 classi top-level: 400.
- Inventario completo dei 400 metodi: [`METODI_STABLE_4.4.4.md`](METODI_STABLE_4.4.4.md).
- `traduzioni.py`: 1.418 righe; lingue presenti: inglese, italiano, spagnolo, francese, tedesco, portoghese e russo.

## Aree originali da trasferire

1. Configurazione, percorsi, cache, preferiti e dati persistenti.
2. Playlist M3U, categorie, URL, ClearKey e varianti.
3. XMLTV/EPG, fusione guide, associazione canali e programmi.
4. TMDB, MusicBrainz, tag, copertine, poster e immagini artisti.
5. Widget originali: ricerca, cursore, guida, tendina, elenco e finestrella.
6. Classe `TV`: libreria, IPTV, controlli, menu, overlay, split, PiP, MPRIS, registrazioni e sottotitoli.
7. Traduzioni e risorse grafiche originali.

## Vincolo

Ogni metodo originale deve essere associato a un modulo di destinazione e mantenuto con la stessa logica. I widget Tkinter vanno adattati a Qt6 conservando aspetto, misure e interazioni. Nessun placeholder conta come funzione migrata. La Stable non va modificata.
