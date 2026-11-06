# XVB Player — Lab

Questa repository è l'ambiente di sviluppo e testing di XVB Player. Le modifiche vengono provate qui prima dell'eventuale trasferimento nella repository Stable.

## Obiettivi

- Sviluppare e verificare il supporto a X11 e Wayland.
- Testare le modifiche senza intervenire sulla versione Stable.
- Preparare e verificare i pacchetti per le principali distribuzioni Linux.
- Portare su Stable soltanto le modifiche che hanno superato i test.

Il progetto mantiene una sola applicazione: Python, Tkinter e libmpv. Non sono previste interfacce parallele o riscritture del player.

## Pacchetti

La repository include tre workflow GitHub Actions:

| Distribuzione | Pacchetto |
|---|---|
| Arch Linux e derivate | `.pkg.tar.zst` |
| Debian e derivate | `.deb` |
| Fedora e derivate | `.rpm` |

Ogni workflow può essere avviato automaticamente quando viene pubblicata una GitHub Release oppure manualmente da **Actions**, indicando il tag da compilare.

Al termine della build, il pacchetto viene allegato alla Release corrispondente. I workflow Debian e Fedora verificano anche che la versione nel tag coincida con quella dichiarata in `xvb.py`.

## Avvio da sorgente

```bash
python3 xvb.py
```

Sono necessarie le dipendenze Python e di sistema di XVB Player, tra cui Tkinter e libmpv.

## Flusso di sviluppo

1. Le modifiche vengono sviluppate e compilate in Lab.
2. I pacchetti vengono installati e testati sulle distribuzioni interessate.
3. Le modifiche verificate possono essere trasferite nella repository Stable.

Lab e Stable sono repository indipendenti. Il lavoro sperimentale non modifica automaticamente Stable.
