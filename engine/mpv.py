import ctypes
import ctypes.util
from core.constants import UA
from PySide6.QtCore import Qt, QTimer, Signal, QByteArray
from PySide6.QtGui import QOpenGLContext, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class _MpvEvent(ctypes.Structure):
    _fields_ = [("event_id", ctypes.c_int), ("error", ctypes.c_int),
                ("reply_userdata", ctypes.c_uint64), ("data", ctypes.c_void_p)]


class _MpvEndFile(ctypes.Structure):
    _fields_ = [("reason", ctypes.c_int), ("error", ctypes.c_int),
                ("playlist_entry_id", ctypes.c_int64),
                ("playlist_insert_id", ctypes.c_int64)]


class MpvError(RuntimeError):
    pass


class MpvVideo(QOpenGLWidget):
    aggiornato = Signal()
    evento = Signal(object)

    MPV_RENDER_PARAM_INVALID = 0
    MPV_RENDER_PARAM_API_TYPE = 1
    MPV_RENDER_PARAM_OPENGL_INIT_PARAMS = 2
    MPV_RENDER_PARAM_OPENGL_FBO = 3
    MPV_RENDER_PARAM_FLIP_Y = 4
    MPV_RENDER_PARAM_BLOCK_FOR_TARGET_TIME = 5
    MPV_RENDER_UPDATE_FRAME = 1
    MPV_EVENT_NONE = 0
    MPV_EVENT_SHUTDOWN = 1
    MPV_EVENT_START_FILE = 6
    MPV_EVENT_END_FILE = 7
    MPV_EVENT_FILE_LOADED = 8
    MPV_EVENT_PLAYBACK_RESTART = 21

    class RenderParam(ctypes.Structure):
        _fields_ = [("type", ctypes.c_int), ("data", ctypes.c_void_p)]

    class OpenGLInitParams(ctypes.Structure):
        _fields_ = [
            ("get_proc_address", ctypes.c_void_p),
            ("get_proc_address_ctx", ctypes.c_void_p),
        ]

    class OpenGLFBO(ctypes.Structure):
        _fields_ = [
            ("fbo", ctypes.c_int),
            ("w", ctypes.c_int),
            ("h", ctypes.c_int),
            ("internal_format", ctypes.c_int),
        ]

    def __init__(self, parent=None, options=None):
        super().__init__(parent)
        formato = QSurfaceFormat()
        formato.setRenderableType(QSurfaceFormat.OpenGL)
        formato.setVersion(3, 2)
        formato.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(formato)
        self.setUpdateBehavior(QOpenGLWidget.NoPartialUpdate)
        self.setFocusPolicy(Qt.StrongFocus)
        self._lib = self._carica_lib()
        self._mpv = None
        self._render = ctypes.c_void_p()
        self._callback = None
        self._proc_callback = None
        self._inizializzato = False
        self._chiuso = False
        self._opzioni = dict(options or {})
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._eventi)
        self._timer.start(15)
        self.aggiornato.connect(self.update, Qt.QueuedConnection)
        self.frameSwapped.connect(self._report_swap)
        self._crea()

    @staticmethod
    def _carica_lib():
        percorso = ctypes.util.find_library("mpv")
        if not percorso:
            raise MpvError("libmpv non è installata")
        lib = ctypes.CDLL(percorso)
        lib.mpv_create.restype = ctypes.c_void_p
        lib.mpv_initialize.argtypes = [ctypes.c_void_p]
        lib.mpv_initialize.restype = ctypes.c_int
        lib.mpv_set_option_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.mpv_set_option_string.restype = ctypes.c_int
        lib.mpv_terminate_destroy.argtypes = [ctypes.c_void_p]
        lib.mpv_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
        lib.mpv_command.restype = ctypes.c_int
        lib.mpv_set_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.mpv_set_property_string.restype = ctypes.c_int
        lib.mpv_get_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.mpv_get_property_string.restype = ctypes.c_void_p
        lib.mpv_free.argtypes = [ctypes.c_void_p]
        lib.mpv_wait_event.argtypes = [ctypes.c_void_p, ctypes.c_double]
        lib.mpv_wait_event.restype = ctypes.c_void_p
        lib.mpv_render_context_create.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
            ctypes.POINTER(MpvVideo.RenderParam)]
        lib.mpv_render_context_create.restype = ctypes.c_int
        lib.mpv_render_context_render.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(MpvVideo.RenderParam)]
        lib.mpv_render_context_render.restype = None
        lib.mpv_render_context_set_update_callback.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        lib.mpv_render_context_set_update_callback.restype = None
        lib.mpv_render_context_update.argtypes = [ctypes.c_void_p]
        lib.mpv_render_context_update.restype = ctypes.c_uint64
        lib.mpv_render_context_free.argtypes = [ctypes.c_void_p]
        lib.mpv_render_context_report_swap.argtypes = [ctypes.c_void_p]
        return lib

    def _crea(self):
        self._mpv = self._lib.mpv_create()
        if not self._mpv:
            raise MpvError("mpv_create non riuscita")
        opzioni = {
            "vo": "libmpv",
            "terminal": "no",
            "input-default-bindings": "no",
            "input-vo-keyboard": "no",
            "hwdec": "auto-safe",
            "keep-open": "yes",
            "cache": "yes",
            "network-timeout": "60",
            "ytdl": "no",
            "user-agent": UA,
            "volume-max": "150",
            "cursor-autohide": "3000",
            "stream-lavf-o": "reconnect=1,reconnect_streamed=1,reconnect_on_network_error=1,reconnect_delay_max=10",
        }
        opzioni.update(self._opzioni)
        for nome, valore in opzioni.items():
            rc = self._lib.mpv_set_option_string(
                self._mpv, str(nome).encode(), str(valore).encode())
            if rc < 0:
                self.chiudi()
                raise MpvError("Opzione mpv non valida: " + str(nome))
        rc = self._lib.mpv_initialize(self._mpv)
        if rc < 0:
            self.chiudi()
            raise MpvError("Inizializzazione libmpv fallita: %d" % rc)
        self._lib.mpv_set_property_string(self._mpv, b"window-dragging", b"no")
        self._lib.mpv_set_property_string(self._mpv, b"audio-display", b"embedded-first")

    def initializeGL(self):
        if self._inizializzato or not self._mpv:
            return
        def get_proc(_ctx, nome):
            ptr = QOpenGLContext.currentContext().getProcAddress(QByteArray(nome))
            if ptr is None:
                return None
            try:
                return ctypes.cast(int(ptr), ctypes.c_void_p).value
            except (TypeError, ValueError):
                return ctypes.cast(ptr, ctypes.c_void_p).value
        self._proc_callback = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)(get_proc)
        init = self.OpenGLInitParams(
            ctypes.cast(self._proc_callback, ctypes.c_void_p), None)
        api = ctypes.c_char_p(b"opengl")
        params = (self.RenderParam * 3)(
            self.RenderParam(self.MPV_RENDER_PARAM_API_TYPE,
                             ctypes.cast(ctypes.pointer(api), ctypes.c_void_p)),
            self.RenderParam(self.MPV_RENDER_PARAM_OPENGL_INIT_PARAMS,
                             ctypes.cast(ctypes.pointer(init), ctypes.c_void_p)),
            self.RenderParam(self.MPV_RENDER_PARAM_INVALID, None))
        rc = self._lib.mpv_render_context_create(
            ctypes.byref(self._render), self._mpv, params)
        if rc < 0:
            raise MpvError("Creazione contesto render mpv fallita: %d" % rc)
        def aggiornamento(_ctx):
            self.aggiornato.emit()
        self._callback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(aggiornamento)
        self._lib.mpv_render_context_set_update_callback(
            self._render, ctypes.cast(self._callback, ctypes.c_void_p), None)
        self._inizializzato = True

    def paintGL(self):
        if not self._render:
            return
        self._lib.mpv_render_context_update(self._render)
        fbo = self.OpenGLFBO(
            int(self.defaultFramebufferObject()),
            int(self.width() * self.devicePixelRatioF()),
            int(self.height() * self.devicePixelRatioF()), 0x8058)
        flip = ctypes.c_int(1)
        params = (self.RenderParam * 3)(
            self.RenderParam(self.MPV_RENDER_PARAM_OPENGL_FBO,
                             ctypes.cast(ctypes.pointer(fbo), ctypes.c_void_p)),
            self.RenderParam(self.MPV_RENDER_PARAM_FLIP_Y,
                             ctypes.cast(ctypes.pointer(flip), ctypes.c_void_p)),
            self.RenderParam(self.MPV_RENDER_PARAM_INVALID, None))
        self._lib.mpv_render_context_render(self._render, params)


    def _report_swap(self):
        if self._render:
            self._lib.mpv_render_context_report_swap(self._render)

    def resizeGL(self, w, h):
        self.update()

    def _comando(self, *argomenti):
        if not self._mpv:
            raise MpvError("Player non inizializzato")
        valori = [str(x).encode("utf-8") for x in argomenti] + [None]
        argv = (ctypes.c_char_p * len(valori))(*valori)
        rc = self._lib.mpv_command(self._mpv, argv)
        if rc < 0:
            raise MpvError("Comando mpv fallito: %d" % rc)
        return rc

    def apri(self, url, modo="replace"):
        self._comando("loadfile", url, modo)

    def pausa(self, valore=None):
        if valore is None:
            self._comando("cycle", "pause")
        else:
            self._proprieta("pause", "yes" if valore else "no")

    def ferma(self):
        self._comando("stop")

    def seek(self, secondi, assoluto=True):
        self._comando("seek", secondi, "absolute" if assoluto else "relative")

    def volume(self, valore):
        self._proprieta("volume", valore)

    def _proprieta(self, nome, valore):
        rc = self._lib.mpv_set_property_string(
            self._mpv, str(nome).encode(), str(valore).encode())
        if rc < 0:
            raise MpvError("Impossibile impostare " + str(nome))

    def leggi(self, nome):
        ptr = self._lib.mpv_get_property_string(self._mpv, str(nome).encode())
        if not ptr:
            return None
        try:
            return ctypes.string_at(ptr).decode("utf-8", "replace")
        finally:
            self._lib.mpv_free(ptr)

    def _eventi(self):
        if not self._mpv:
            return
        for _ in range(32):
            puntatore = self._lib.mpv_wait_event(self._mpv, 0.0)
            if not puntatore:
                break
            evento = ctypes.cast(puntatore, ctypes.POINTER(_MpvEvent)).contents
            if evento.event_id == self.MPV_EVENT_NONE:
                break
            dati = {"id": evento.event_id, "errore": evento.error,
                    "userdata": evento.reply_userdata}
            if evento.event_id == self.MPV_EVENT_END_FILE and evento.data:
                fine = ctypes.cast(evento.data, ctypes.POINTER(_MpvEndFile)).contents
                dati["motivo"] = fine.reason
                dati["errore_file"] = fine.error
            self.evento.emit(dati)


    @property
    def time_pos(self):
        try:
            return float(self.leggi("time-pos") or 0)
        except (TypeError, ValueError):
            return 0.0

    @property
    def duration(self):
        try:
            return float(self.leggi("duration") or 0)
        except (TypeError, ValueError):
            return 0.0

    def comando(self, *argomenti):
        return self._comando(*argomenti)

    def imposta(self, nome, valore):
        self._proprieta(nome, valore)

    def ciclo(self, nome):
        self._comando("cycle", nome)

    def regola(self, nome, valore):
        self._comando("add", nome, valore)

    def closeEvent(self, evento):
        self.chiudi()
        super().closeEvent(evento)

    def chiudi(self):
        if self._chiuso:
            return
        self._chiuso = True
        self._timer.stop()
        if self._render:
            try:
                self.makeCurrent()
                self._lib.mpv_render_context_free(self._render)
                self.doneCurrent()
            except Exception:
                self._lib.mpv_render_context_free(self._render)
            self._render = ctypes.c_void_p()
        if self._mpv:
            self._lib.mpv_terminate_destroy(self._mpv)
            self._mpv = None
