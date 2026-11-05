import sys

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.mpv import MPVEngine
from engine.render import MPVRenderWidget


class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("XVB Lab")
        self.resize(1000, 650)

        self.video = MPVRenderWidget(engine, self)
        self.video.setMinimumSize(320, 180)

        open_button = QPushButton("Apri file")
        open_button.clicked.connect(self.open_file)
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.engine.stop)

        controls = QHBoxLayout()
        controls.addWidget(open_button)
        controls.addWidget(stop_button)
        controls.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video, 1)
        layout.addLayout(controls)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Apri file multimediale")
        if path:
            self.engine.load(path)

    def closeEvent(self, event):
        self.video.close_render_context()
        self.engine.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    engine = MPVEngine()
    window = MainWindow(engine)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
