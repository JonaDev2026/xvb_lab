# XVB Player — laboratorio Wayland

Questa repository contiene una sola applicazione: la copia della Stable 4.4.4, mantenuta il più possibile identica.

Obiettivo: far funzionare la stessa applicazione su X11 e Wayland. Non è prevista una riscrittura Qt, una seconda interfaccia o una seconda implementazione del player.

Il lavoro procede con modifiche piccole e verificabili, intervenendo solo sui punti necessari alla compatibilità grafica. Le funzioni, i menu e il comportamento della Stable restano il riferimento.

## Avvio

```bash
python3 xvb.py
```

Servono le dipendenze Python e di sistema già richieste da XVB Stable 4.4.4, inclusi Tkinter e libmpv.

Questa è una copia sperimentale indipendente: non modifica la repository né il rilascio Stable.
