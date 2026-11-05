import ctypes
from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget


MPV_RENDER_PARAM_API_TYPE = 1
MPV_RENDER_PARAM_OPENGL_INIT_PARAMS = 2
MPV_RENDER_PARAM_OPENGL_FBO = 3
MPV_RENDER_PARAM_FLIP_Y = 4


class RenderParam(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("data", ctypes.c_void_p)]


GET_PROC_ADDRESS = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p
)
UPDATE_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p)


class OpenGLInitParams(ctypes.Structure):
    _fields_ = [
        ("get_proc_address", GET_PROC_ADDRESS),
        ("get_proc_address_ctx", ctypes.c_void_p),
    ]


class OpenGLFBO(ctypes.Structure):
    _fields_ = [
        ("fbo", ctypes.c_int),
        ("w", ctypes.c_int),
        ("h", ctypes.c_int),
        ("internal_format", ctypes.c_int),
    ]


class MPVRenderWidget(QOpenGLWidget):
    frame_available = Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._render_context = ctypes.c_void_p()
        self._get_proc_callback = None
        self._update_callback = None
        self._closed = False
        self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.NoPartialUpdate)
        self.frame_available.connect(self.update, Qt.ConnectionType.QueuedConnection)

    def _configure_render_api(self):
        lib = self.engine.library
        lib.mpv_render_context_create.restype = ctypes.c_int
        lib.mpv_render_context_create.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
            ctypes.POINTER(RenderParam),
        ]
        lib.mpv_render_context_set_update_callback.restype = None
        lib.mpv_render_context_set_update_callback.argtypes = [
            ctypes.c_void_p, UPDATE_CALLBACK, ctypes.c_void_p
        ]
        lib.mpv_render_context_render.restype = ctypes.c_int
        lib.mpv_render_context_render.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(RenderParam)
        ]
        lib.mpv_render_context_free.restype = None
        lib.mpv_render_context_free.argtypes = [ctypes.c_void_p]

    def _get_proc_address(self, _ctx, name):
        context = QOpenGLContext.currentContext()
        if context is None:
            return None
        pointer = context.getProcAddress(QByteArray(name))
        if not pointer:
            return None
        try:
            return ctypes.c_void_p(int(pointer)).value
        except (TypeError, ValueError):
            return ctypes.cast(pointer, ctypes.c_void_p).value

    def _on_mpv_update(self, _ctx):
        self.frame_available.emit()

    def initializeGL(self):
        if self._closed:
            return
        self._configure_render_api()
        self._get_proc_callback = GET_PROC_ADDRESS(self._get_proc_address)
        init_params = OpenGLInitParams(self._get_proc_callback, None)
        api_type = ctypes.c_char_p(b"opengl")
        params = (RenderParam * 3)(
            RenderParam(
                MPV_RENDER_PARAM_API_TYPE,
                ctypes.cast(api_type, ctypes.c_void_p),
            ),
            RenderParam(
                MPV_RENDER_PARAM_OPENGL_INIT_PARAMS,
                ctypes.cast(ctypes.pointer(init_params), ctypes.c_void_p),
            ),
            RenderParam(0, None),
        )
        result = self.engine.library.mpv_render_context_create(
            ctypes.byref(self._render_context), self.engine.handle, params
        )
        self.engine.check(result, "mpv_render_context_create")
        self._update_callback = UPDATE_CALLBACK(self._on_mpv_update)
        self.engine.library.mpv_render_context_set_update_callback(
            self._render_context, self._update_callback, None
        )

    def paintGL(self):
        if self._closed or not self._render_context:
            return
        ratio = self.devicePixelRatioF()
        fbo = OpenGLFBO(
            int(self.defaultFramebufferObject()),
            max(1, round(self.width() * ratio)),
            max(1, round(self.height() * ratio)),
            0,
        )
        flip_y = ctypes.c_int(1)
        params = (RenderParam * 3)(
            RenderParam(
                MPV_RENDER_PARAM_OPENGL_FBO,
                ctypes.cast(ctypes.pointer(fbo), ctypes.c_void_p),
            ),
            RenderParam(
                MPV_RENDER_PARAM_FLIP_Y,
                ctypes.cast(ctypes.pointer(flip_y), ctypes.c_void_p),
            ),
            RenderParam(0, None),
        )
        self.engine.check(
            self.engine.library.mpv_render_context_render(
                self._render_context, params
            ),
            "mpv_render_context_render",
        )

    def close_render_context(self):
        if self._closed:
            return
        self._closed = True
        if self._render_context:
            self.makeCurrent()
            self.engine.library.mpv_render_context_set_update_callback(
                self._render_context, UPDATE_CALLBACK(), None
            )
            self.engine.library.mpv_render_context_free(self._render_context)
            self._render_context = ctypes.c_void_p()
            self.doneCurrent()
        self._update_callback = None
        self._get_proc_callback = None
