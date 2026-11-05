import ctypes
import ctypes.util
import threading

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QOpenGLWidget


class _RenderParam(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("data", ctypes.c_void_p)]


class _OpenGLInit(ctypes.Structure):
    _fields_ = [
        ("get_proc_address", ctypes.c_void_p),
        ("get_proc_address_ctx", ctypes.c_void_p),
    ]


class _OpenGLFBO(ctypes.Structure):
    _fields_ = [
        ("fbo", ctypes.c_int),
        ("w", ctypes.c_int),
        ("h", ctypes.c_int),
        ("internal_format", ctypes.c_int),
    ]


class _RenderUpdate(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_uint64)]


_GET_PROC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)
_UPDATE = ctypes.CFUNCTYPE(None, ctypes.c_void_p)


class MpvPlayer(QOpenGLWidget):
    renderUpdate = Signal()
    fileLoaded = Signal()
    endFile = Signal(int)
    playbackRestart = Signal()
    propertyChanged = Signal(str, object)
    error = Signal(str)

    MPV_RENDER_PARAM_API_TYPE = 1
    MPV_RENDER_PARAM_OPENGL_INIT_PARAMS = 2
    MPV_RENDER_PARAM_OPENGL_FBO = 3
    MPV_RENDER_PARAM_FLIP_Y = 4
    MPV_RENDER_PARAM_INVALID = 0

    MPV_EVENT_NONE = 0
    MPV_EVENT_SHUTDOWN = 1
    MPV_EVENT_FILE_LOADED = 8
    MPV_EVENT_END_FILE = 7
    MPV_EVENT_PLAYBACK_RESTART = 21
    MPV_EVENT_PROPERTY_CHANGE = 22

    def __init__(self, parent=None, mpv_path=None, options=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        self.setUpdateBehavior(QOpenGLWidget.NoPartialUpdate)
        self.setFocusPolicy(Qt.StrongFocus)
        self._lib = self._load_library(mpv_path)
        self._configure_api()
        self._handle = self._lib.mpv_create()
        if not self._handle:
            raise RuntimeError("mpv_create() non riuscita")
        predefinite = {
            "vo": "libmpv",
            "terminal": "no",
            "msg-level": "all=no",
            "keep-open": "yes",
            "input-default-bindings": "no",
            "input-vo-keyboard": "no",
        }
        if options:
            predefinite.update(options)
        for nome, valore in predefinite.items():
            self._check(self._lib.mpv_set_option_string(
                self._handle, nome.encode(), str(valore).encode()))
        self._check(self._lib.mpv_initialize(self._handle))
        self._render = ctypes.c_void_p()
        self._render_callback = _UPDATE(self._aggiorna_da_mpv)
        self.renderUpdate.connect(self.update, Qt.QueuedConnection)
        self._get_proc_callback = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._eventi)
        self._timer.start(10)
        self._osservate = set()\n        self._nomi_osservati = {}
        self._chiuso = False

    @staticmethod
    def _load_library(percorso):
        nome = percorso or ctypes.util.find_library("mpv")
        if not nome:
            raise RuntimeError("libmpv non trovata")
        return ctypes.CDLL(nome)

    def _configure_api(self):
        lib = self._lib
        lib.mpv_create.restype = ctypes.c_void_p
        lib.mpv_set_option_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.mpv_set_option_string.restype = ctypes.c_int
        lib.mpv_initialize.argtypes = [ctypes.c_void_p]
        lib.mpv_initialize.restype = ctypes.c_int
        lib.mpv_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
        lib.mpv_command.restype = ctypes.c_int
        lib.mpv_set_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.mpv_set_property_string.restype = ctypes.c_int
        lib.mpv_get_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.mpv_get_property_string.restype = ctypes.c_void_p
        lib.mpv_free.argtypes = [ctypes.c_void_p]
        lib.mpv_wait_event.argtypes = [ctypes.c_void_p, ctypes.c_double]
        lib.mpv_wait_event.restype = ctypes.c_void_p
        lib.mpv_observe_property.argtypes = [ctypes.c_void_p, ctypes.c_uint64,
                                             ctypes.c_char_p, ctypes.c_int]
        lib.mpv_observe_property.restype = ctypes.c_int
        lib.mpv_render_context_create.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
            ctypes.POINTER(_RenderParam)]
        lib.mpv_render_context_create.restype = ctypes.c_int
        lib.mpv_render_context_set_update_callback.argtypes = [
            ctypes.c_void_p, _UPDATE, ctypes.c_void_p]
        lib.mpv_render_context_render.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(_RenderParam)]
        lib.mpv_render_context_render.restype = ctypes.c_int
        lib.mpv_render_context_report_swap.argtypes = [ctypes.c_void_p]
        lib.mpv_render_context_free.argtypes = [ctypes.c_void_p]
        lib.mpv_terminate_destroy.argtypes = [ctypes.c_void_p]

    def _check(self, codice):
        if codice < 0:
            self.error.emit("libmpv: errore %d" % codice)
            raise RuntimeError("Errore libmpv: %d" % codice)
        return codice

    def initializeGL(self):
        if self._render:
            return
        ctx = self.context()

        @_GET_PROC
        def get_proc(_contesto, nome):
            indirizzo = ctx.getProcAddress(nome.decode("ascii"))
            if not indirizzo:
                return None
            return int(indirizzo)

        self._get_proc_callback = get_proc
        init = _OpenGLInit(
            ctypes.cast(get_proc, ctypes.c_void_p).value, None)
        api = ctypes.c_char_p(b"opengl")
        params = (_RenderParam * 3)(
            _RenderParam(self.MPV_RENDER_PARAM_API_TYPE,
                         ctypes.cast(ctypes.pointer(api), ctypes.c_void_p)),
            _RenderParam(self.MPV_RENDER_PARAM_OPENGL_INIT_PARAMS,
                         ctypes.cast(ctypes.pointer(init), ctypes.c_void_p)),
            _RenderParam(self.MPV_RENDER_PARAM_INVALID, None))
        self._check(self._lib.mpv_render_context_create(
            ctypes.byref(self._render), self._handle, params))
        self._lib.mpv_render_context_set_update_callback(
            self._render, self._render_callback, None)

    def paintGL(self):
        if not self._render:
            return
        scala = self.devicePixelRatioF()
        fbo = _OpenGLFBO(
            int(self.defaultFramebufferObject()), int(self.width() * scala),
            int(self.height() * scala), 0x8058)
        flip = ctypes.c_int(1)
        params = (_RenderParam * 3)(
            _RenderParam(self.MPV_RENDER_PARAM_OPENGL_FBO,
                         ctypes.cast(ctypes.pointer(fbo), ctypes.c_void_p)),
            _RenderParam(self.MPV_RENDER_PARAM_FLIP_Y,
                         ctypes.cast(ctypes.pointer(flip), ctypes.c_void_p)),
            _RenderParam(self.MPV_RENDER_PARAM_INVALID, None))
        self._lib.mpv_render_context_render(self._render, params)
        self._lib.mpv_render_context_report_swap(self._render)

    def _aggiorna_da_mpv(self, _ctx):
        self.renderUpdate.emit()

    def _eventi(self):
        if not self._handle or self._chiuso:
            return
        for _ in range(32):
            puntatore = self._lib.mpv_wait_event(self._handle, 0.0)
            if not puntatore:
                break
            evento = ctypes.cast(puntatore, ctypes.POINTER(_Event)).contents
            if evento.event_id == self.MPV_EVENT_NONE:
                break
            if evento.event_id == self.MPV_EVENT_FILE_LOADED:
                self.fileLoaded.emit()
            elif evento.event_id == self.MPV_EVENT_END_FILE:
                dati = ctypes.cast(evento.data, ctypes.POINTER(_EndFile)).contents
                self.endFile.emit(dati.reason)
            elif evento.event_id == self.MPV_EVENT_PLAYBACK_RESTART:
                self.playbackRestart.emit()
            elif evento.event_id == self.MPV_EVENT_PROPERTY_CHANGE and evento.data:
                dati = ctypes.cast(evento.data, ctypes.POINTER(_Property)).contents
                nome = self._nomi_osservati.get(dati.reply_userdata)
                if nome:
                    valore = self._leggi_valore(dati)
                    self.propertyChanged.emit(nome, valore)

    def _leggi_valore(self, dati):
        if not dati.data:
            return None
        if dati.format == 1:
            return ctypes.cast(dati.data, ctypes.c_char_p).value.decode("utf-8", "replace")
        if dati.format == 3:
            return bool(ctypes.cast(dati.data, ctypes.POINTER(ctypes.c_int)).contents.value)
        if dati.format == 4:
            return ctypes.cast(dati.data, ctypes.POINTER(ctypes.c_longlong)).contents.value
        if dati.format == 5:
            return ctypes.cast(dati.data, ctypes.POINTER(ctypes.c_double)).contents.value
        return None

    def comando(self, *argomenti):
        valori = [str(v).encode("utf-8") for v in argomenti] + [None]
        array = (ctypes.c_char_p * len(valori))(*valori)
        return self._check(self._lib.mpv_command(self._handle, array))

    def apri(self, url, modo="replace"):
        self.comando("loadfile", url, modo)

    def play(self):
        self.set_proprieta("pause", "no")

    def pausa(self):
        self.set_proprieta("pause", "yes")

    def toggle_pause(self):
        self.comando("cycle", "pause")

    def stop(self):
        self.comando("stop")

    def seek(self, secondi, modalita="absolute"):
        self.comando("seek", secondi, modalita)

    def volume(self, valore):
        self.set_proprieta("volume", valore)

    def set_proprieta(self, nome, valore):
        return self._check(self._lib.mpv_set_property_string(
            self._handle, nome.encode(), str(valore).encode()))

    def proprieta(self, nome):
        ptr = self._lib.mpv_get_property_string(self._handle, nome.encode())
        if not ptr:
            return None
        try:
            return ctypes.string_at(ptr).decode("utf-8", "replace")
        finally:
            self._lib.mpv_free(ptr)

    def osserva(self, nome):
        if nome in self._osservate:
            return
        uid = len(self._osservate) + 1
        self._nomi_osservati[uid] = nome
        self._check(self._lib.mpv_observe_property(
            self._handle, uid, nome.encode(), 0))
        self._osservate.add(nome)

    def closeEvent(self, evento):
        self.chiudi()
        super().closeEvent(evento)

    def chiudi(self):
        if self._chiuso:
            return
        self._chiuso = True
        self._timer.stop()
        if self._render:
            self._lib.mpv_render_context_set_update_callback(self._render, None, None)
            self._lib.mpv_render_context_free(self._render)
            self._render = ctypes.c_void_p()
        if self._handle:
            self._lib.mpv_terminate_destroy(self._handle)
            self._handle = None


class _Event(ctypes.Structure):
    _fields_ = [("event_id", ctypes.c_int), ("error", ctypes.c_int),
                ("reply_userdata", ctypes.c_uint64), ("data", ctypes.c_void_p)]


class _EndFile(ctypes.Structure):
    _fields_ = [("reason", ctypes.c_int), ("error", ctypes.c_int),
                ("playlist_entry_id", ctypes.c_int64),
                ("playlist_insert_id", ctypes.c_int64)]


class _Property(ctypes.Structure):
    _fields_ = [("name", ctypes.c_char_p), ("format", ctypes.c_int),
                ("data", ctypes.c_void_p)]
