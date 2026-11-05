# XVB Lab — Progressione

## Stato

**Reset eseguito il 2026-11-05.**

La precedente implementazione di XVB Lab è stata azzerata. Il codice precedente non costituisce più la base del progetto e non va ripreso come architettura o come riferimento funzionale.

## Regola di sviluppo

La base funzionale è esclusivamente **XVB Stable 4.4.4**, tag `v4.4.4`, repository https://github.com/JonaDev2026/xvb.

XVB Lab deve essere una migrazione fedele dell'applicazione originale:
- tutte le funzioni e i comportamenti della Stable;
- stessa interfaccia, disposizione, menu, icone, controlli e flussi d'uso;
- nessuna funzione inventata, eliminata, semplificata o sostituita da placeholder;
- moduli separati per responsabilità;
- PySide6 / Qt6 al posto di Tkinter;
- libmpv Render API;
- compatibilità X11 e Wayland.

Non si parte da un player dimostrativo per aggiungere gradualmente funzioni. Si parte dall'inventario completo del codice Stable e si trasferiscono le sue funzioni, mantenendo la corrispondenza tra originale e modulo Qt.

## Sequenza obbligatoria

1. Analizzare integralmente Stable 4.4.4 e inventariare classi, funzioni, callback, menu, risorse, configurazione e dipendenze.
2. Definire la mappa di migrazione: funzione originale, modulo di destinazione, adattamento Qt/libmpv e verifica prevista.
3. Progettare e verificare il rendering Qt/libmpv su X11 e Wayland prima di ricostruire la finestra completa.
4. Ricostruire l'interfaccia originale e collegare le funzioni migrate.
5. Verificare ogni funzione rispetto alla Stable e registrare test e differenze reali.

## Registro lavori

Nessuna funzione è dichiarata migrata o verificata in questa nuova ripartenza. Le attività iniziano da zero dopo l'inventario completo della Stable.
