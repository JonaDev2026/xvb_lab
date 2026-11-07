# Diario di sviluppo — XVB Lab 4.4.6 Testing

## Base di partenza

- Sorgente ricostruito dal tag ufficiale Stable `v4.4.5`.
- `xvb.py` coincide integralmente con quello Stable 4.4.5, con la sola versione impostata a `4.4.6`.
- `traduzioni.py` è identico alla Stable 4.4.5.
- Il supporto Wayland è già incluso nella base Stable 4.4.5: non viene mantenuta una patch separata.
- Restano nel repository Lab i workflow dedicati alla creazione dei pacchetti Arch, Debian e Fedora.

## Regole

- Sviluppo esclusivamente in `JonaDev2026/xvb_lab`.
- Il repository Stable `JonaDev2026/xvb` non deve essere modificato.
- Una sola applicazione: Python, Tkinter e libmpv.
- Nessun refactoring o cambiamento a interfaccia, IPTV, EPG, playlist, musica, video e controlli senza una richiesta specifica.
- Ogni modifica sperimentale deve essere circoscritta e verificata prima di passare alla Stable.

## Stato iniziale 4.4.6

- Ricostruzione completata dalla Stable 4.4.5.
- Le modifiche sperimentali precedenti alla lista EPG non sono state riportate.
- Nessuna modifica funzionale aggiuntiva applicata.
- Da questa base pulita riparte lo sviluppo della 4.4.6 Testing.
