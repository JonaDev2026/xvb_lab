import threading
from urllib.parse import quote

try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib
    HA_MPRIS = True
except Exception:
    HA_MPRIS = False

try:
    from PySide6.QtCore import QObject, Qt, Signal
    HA_QT = True
except ImportError:
    HA_QT = False

MPRIS_RADICE = "org.mpris.MediaPlayer2"
MPRIS_PLAYER = "org.mpris.MediaPlayer2.Player"
MPRIS_PROP = "org.freedesktop.DBus.Properties"


if HA_QT:
    class _QtDispatcher(QObject):
        invoke = Signal(object, object)

        def __init__(self):
            super().__init__()
            self.invoke.connect(self._esegui, Qt.ConnectionType.QueuedConnection)

        def _esegui(self, funzione, argomenti):
            funzione(*argomenti)



def avvia_mpris(app, dispatcher=None):
    if not HA_MPRIS or not HA_QT:
        return None
    try:
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        nome = dbus.service.BusName(MPRIS_RADICE + ".xvb5", bus, do_not_queue=True)
    except Exception:
        return None

    dispatcher = dispatcher or _QtDispatcher()
    app._mpris_dispatcher = dispatcher

    class Mpris(dbus.service.Object):
        def __init__(self):
            super().__init__(nome, "/org/mpris/MediaPlayer2")
            self.stato = {}

        def qt(self, funzione, *argomenti):
            dispatcher.invoke.emit(funzione, argomenti)

        @dbus.service.method(MPRIS_RADICE)
        def Raise(self):
            self.qt(app.mpris_alza)

        @dbus.service.method(MPRIS_RADICE)
        def Quit(self):
            self.qt(app.chiudi)

        @dbus.service.method(MPRIS_PLAYER)
        def Next(self):
            self.qt(app.salta, +1)

        @dbus.service.method(MPRIS_PLAYER)
        def Previous(self):
            self.qt(app.salta, -1)

        @dbus.service.method(MPRIS_PLAYER)
        def PlayPause(self):
            self.qt(app.mpris_comando, "playpause")

        @dbus.service.method(MPRIS_PLAYER)
        def Play(self):
            self.qt(app.mpris_comando, "play")

        @dbus.service.method(MPRIS_PLAYER)
        def Pause(self):
            self.qt(app.mpris_comando, "pause")

        @dbus.service.method(MPRIS_PLAYER)
        def Stop(self):
            self.qt(app.ferma)

        @dbus.service.method(MPRIS_PLAYER, in_signature="x")
        def Seek(self, us):
            self.qt(app.avanza, int(us) / 1e6)

        @dbus.service.method(MPRIS_PLAYER, in_signature="ox")
        def SetPosition(self, _traccia, us):
            self.qt(app.mpris_posizione, int(us) / 1e6)

        @dbus.service.method(MPRIS_PLAYER, in_signature="s")
        def OpenUri(self, uri):
            self.qt(app.apri, uri)

        @dbus.service.signal(MPRIS_PLAYER, signature="x")
        def Seeked(self, us):
            pass

        def tutte(self, iface):
            if iface == MPRIS_RADICE:
                return dbus.Dictionary({
                    "CanQuit": True, "CanRaise": True, "HasTrackList": False,
                    "Identity": "XVB Player", "DesktopEntry": "xvb5",
                    "SupportedUriSchemes": dbus.Array(["file", "http", "https", "rtsp", "rtmp"], signature="s"),
                    "SupportedMimeTypes": dbus.Array([], signature="s"),
                }, signature="sv")
            if iface != MPRIS_PLAYER:
                return dbus.Dictionary({}, signature="sv")
            stato = self.stato
            meta = {"mpris:trackid": dbus.ObjectPath("/org/xvb5/track/%d" % stato.get("giro", 0))}
            if stato.get("titolo"):
                meta["xesam:title"] = stato["titolo"]
            if stato.get("artista"):
                meta["xesam:artist"] = dbus.Array([stato["artista"]], signature="s")
            if stato.get("album"):
                meta["xesam:album"] = stato["album"]
            if stato.get("arte"):
                meta["mpris:artUrl"] = "file://" + quote(stato["arte"])
            if stato.get("durata"):
                meta["mpris:length"] = dbus.Int64(int(stato["durata"] * 1e6))
            try:
                posizione = int((app.mpv.time_pos or 0) * 1e6)
            except Exception:
                posizione = 0
            return dbus.Dictionary({
                "PlaybackStatus": stato.get("stato", "Stopped"),
                "LoopStatus": stato.get("giro_ripeti", "None"),
                "Rate": 1.0, "MinimumRate": 1.0, "MaximumRate": 1.0,
                "Shuffle": bool(stato.get("shuffle")),
                "Metadata": dbus.Dictionary(meta, signature="sv"),
                "Volume": float(stato.get("volume", 1.0)),
                "Position": dbus.Int64(posizione),
                "CanGoNext": True, "CanGoPrevious": True,
                "CanPlay": True, "CanPause": True,
                "CanSeek": bool(stato.get("durata")), "CanControl": True,
            }, signature="sv")

        @dbus.service.method(MPRIS_PROP, in_signature="ss", out_signature="v")
        def Get(self, iface, prop):
            return self.tutte(iface)[prop]

        @dbus.service.method(MPRIS_PROP, in_signature="s", out_signature="a{sv}")
        def GetAll(self, iface):
            return self.tutte(iface)

        @dbus.service.method(MPRIS_PROP, in_signature="ssv")
        def Set(self, iface, prop, valore):
            if prop == "Volume":
                self.qt(app.volume.setValue, int(max(0.0, min(1.5, float(valore))) * 100))
            elif prop == "Shuffle":
                self.qt(app.mpris_shuffle, bool(valore))
            elif prop == "LoopStatus":
                self.qt(app.metti_ripeti,
                        {"Track": "uno", "Playlist": "tutti"}.get(str(valore), ""))

        @dbus.service.signal(MPRIS_PROP, signature="sa{sv}as")
        def PropertiesChanged(self, iface, cambiati, tolti):
            pass

        def aggiorna(self, stato):
            if stato == self.stato:
                return
            self.stato = stato

            def manda():
                try:
                    tutto = self.tutte(MPRIS_PLAYER)
                    del tutto["Position"]
                    self.PropertiesChanged(MPRIS_PLAYER, tutto, dbus.Array([], signature="s"))
                except Exception:
                    pass
                return False
            GLib.idle_add(manda)

    try:
        servizio = Mpris()
    except Exception:
        return None
    threading.Thread(target=GLib.MainLoop().run, daemon=True).start()
    return servizio
