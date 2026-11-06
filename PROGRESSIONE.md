# Diario di sviluppo — compatibilità X11 e Wayland

## Punto di partenza

- Base unica: XVB Player Stable 4.4.4, tag `v4.4.4`.
- File applicativo: `xvb.py`, copiato dalla Stable senza riscritture.
- Modulo necessario: `traduzioni.py`.
- Interfaccia, logica IPTV, EPG, musica, video e controlli restano quelli della Stable.
- Nessuna versione Qt/PySide6 parallela e nessuna seconda implementazione del player.

## Obiettivo

La stessa applicazione deve funzionare sia su X11 sia su Wayland, mantenendo l'interfaccia e le funzioni della Stable.

## Metodo

1. Verificare la copia della Stable e le sue risorse.
2. Individuare il punto preciso che impedisce il corretto funzionamento su Wayland.
3. Applicare una modifica circoscritta, senza cambiare il percorso X11 se non necessario.
4. Verificare su X11 e Wayland dopo ogni intervento.
5. Annotare qui ogni modifica, il motivo e il risultato dei test.

## Regola del progetto

Una sola applicazione e un solo codice sorgente. Niente ricostruzioni, fork interni, interfacce alternative o refactoring non indispensabili.

## Stato iniziale

- Copia della Stable 4.4.4 importata.
- Nessuna modifica di compatibilità Wayland ancora applicata.
- Stable originale e relativo repository non modificati.


### 2026-11-06 — Primo intervento mirato

- La documentazione di mpv specifica che `wid` identifica una finestra X11; il contesto grafico Wayland non può usare quell'ID come superficie nativa.
- Tkinter continua a usare la finestra X11 tramite XWayland nella sessione Wayland.
- Aggiunta una selezione condizionale del contesto `x11egl` per libmpv solo quando sono presenti sia `WAYLAND_DISPLAY` sia `DISPLAY`.
- Applicata sia al player principale sia al secondo player dello split screen.
- In sessione X11 non viene impostata alcuna nuova opzione.
- Nessuna modifica a layout, controlli, funzioni o logica di riproduzione.
- Verifica statica: entrambi i costruttori MPV ricevono la stessa selezione condizionale.
- Verifica reale ancora necessaria: avvio e riproduzione in Wayland, fullscreen, ridimensionamento, split screen e conferma che il video resti incorporato nella finestra XVB.

## Test locale richiesto

1. In una sessione Wayland, avviare XVB dal terminale e verificare che il video resti nell'area video della finestra principale.
2. Provare apertura di un canale IPTV o di un file locale, ridimensionamento e fullscreen.
3. Provare split screen e chiuderlo.
4. Ripetere l'avvio in X11 per confermare che il comportamento Stable non sia cambiato.
5. Se il video resta separato o compare un errore di contesto, inviare il log `~/.cache/xvb/xvb.log`.
