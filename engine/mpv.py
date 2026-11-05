import ctypes
import ctypes.util


class MPVError(RuntimeError):
    pass


class MPVEngine:
    def __init__(self, options=None):
        library = ctypes.util.find_library("mpv")
        if not library:
            raise MPVError("libmpv non trovato. Installare la libreria runtime di mpv.")

        self._lib = ctypes.CDLL(library)
        self._handle = None
        self._configure_api()
        self._handle = self._lib.mpv_create()
        if not self._handle:
            raise MPVError("Impossibile creare l'istanza libmpv.")

        configured = {"vo": "libmpv"}
        configured.update(options or {})
        try:
            for name, value in configured.items():
                self._set_option(name, value)
            self.check(self._lib.mpv_initialize(self._handle), "mpv_initialize")
        except Exception:
            self._lib.mpv_terminate_destroy(self._handle)
            self._handle = None
            raise

    def _configure_api(self):
        self._lib.mpv_create.restype = ctypes.c_void_p
        self._lib.mpv_create.argtypes = []
        self._lib.mpv_set_option_string.restype = ctypes.c_int
        self._lib.mpv_set_option_string.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
        ]
        self._lib.mpv_initialize.restype = ctypes.c_int
        self._lib.mpv_initialize.argtypes = [ctypes.c_void_p]
        self._lib.mpv_command.restype = ctypes.c_int
        self._lib.mpv_command.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)
        ]
        self._lib.mpv_terminate_destroy.restype = None
        self._lib.mpv_terminate_destroy.argtypes = [ctypes.c_void_p]
        self._lib.mpv_error_string.restype = ctypes.c_char_p
        self._lib.mpv_error_string.argtypes = [ctypes.c_int]

    @property
    def library(self):
        return self._lib

    @property
    def handle(self):
        return self._handle

    def check(self, code, operation):
        if code < 0:
            message = self._lib.mpv_error_string(code)
            detail = message.decode("utf-8", "replace") if message else str(code)
            raise MPVError(f"{operation}: {detail}")

    def _set_option(self, name, value):
        result = self._lib.mpv_set_option_string(
            self._handle,
            str(name).encode("utf-8"),
            str(value).encode("utf-8"),
        )
        self.check(result, f"mpv_set_option_string({name})")

    def command(self, *args):
        if not self._handle:
            raise MPVError("Motore non inizializzato.")
        encoded = [str(arg).encode("utf-8") for arg in args]
        argv = (ctypes.c_char_p * (len(encoded) + 1))(*encoded, None)
        self.check(self._lib.mpv_command(self._handle, argv), "mpv_command")

    def load(self, path):
        self.command("loadfile", path, "replace")

    def stop(self):
        self.command("stop")

    def close(self):
        if self._handle:
            self._lib.mpv_terminate_destroy(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
