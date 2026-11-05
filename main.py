import locale
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from engine.mpv import MPVEngine
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, "C")
    app.setApplicationName("XVB")
    root = Path(__file__).resolve().parent
    font_path = root / "resources" / "fonts" / "static" / "GoogleSans-Regular.ttf"
    if font_path.is_file():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
        if families:
            app.setFont(QFont(families[0], 10))
    icon_path = root / "resources" / "icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    engine = MPVEngine()
    window = MainWindow(engine)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
