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
