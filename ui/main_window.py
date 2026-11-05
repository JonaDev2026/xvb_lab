from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSlider,
    QSplitter,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.render import MPVRenderWidget


FONDO = "#1c1b22"
PANNELLO = "#1c1b22"
BARRA = "#1c1b22"
STATO = "#121217"
TASTO = "#2c2c2c"
SCELTO = "#0071e3"
ZEBRA = "#2b2a33"
TESTO = "#e0e0e0"
GRIGIO = "#9e9e9e"
ACCENTO = "#bb86fc"
IN_ONDA = "#42414d"
IN_ONDA2 = "#2b2338"
TESTO_ONDA = "#e9ddff"


class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.resource_dir = Path(__file__).resolve().parents[1] / "resources"
        self.icons_dir = self.resource_dir / "icons"
        self.setWindowTitle("XVB v4.4.4")
        self.resize(1280, 720)
        self.setMinimumSize(900, 520)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {FONDO};
                color: {TESTO};
                font-size: 10pt;
            }}
            QMenuBar {{
                background: {FONDO};
                color: #ffffff;
                border: 0;
                spacing: 2px;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 6px 9px;
            }}
            QMenuBar::item:selected, QMenu::item:selected {{
                background: {IN_ONDA};
                color: #ffffff;
            }}
            QMenu {{
                background: {FONDO};
                color: {TESTO};
                border: 1px solid #34323c;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 10px;
            }}
            QMenu::separator {{
                height: 1px;
                background: #34323c;
                margin: 4px 7px;
            }}
            QLineEdit, QTreeWidget {{
                background: {PANNELLO};
                color: {TESTO};
                border: 0;
                selection-background-color: {SCELTO};
                selection-color: #ffffff;
            }}
            QLineEdit {{
                background: {IN_ONDA};
                border-radius: 4px;
                padding: 7px 9px;
            }}
            QTreeWidget {{
                outline: 0;
                alternate-background-color: {ZEBRA};
            }}
            QTreeWidget::item {{
                min-height: 25px;
                padding: 2px 3px;
            }}
            QSplitter::handle {{
                background: #34323c;
                width: 1px;
            }}
            QPushButton, QToolButton {{
                background: {BARRA};
                color: {TESTO};
                border: 0;
                padding: 4px;
            }}
            QPushButton:hover, QToolButton:hover {{
                color: {ACCENTO};
            }}
            QSlider::groove:horizontal {{
                height: 3px;
                background: #55515f;
            }}
            QSlider::handle:horizontal {{
                background: {TESTO};
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }}
        """)
        self._build_menus()
        self._build_layout()
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start(1000)
        self._update_clock()

    def _icon(self, name):
        path = self.icons_dir / f"{name}.png"
        return QIcon(str(path)) if path.is_file() else QIcon()

    def _action(self, menu, text, callback=None, enabled=True, shortcut=None):
        action = QAction(text, self)
        if callback is not None:
            action.triggered.connect(callback)
        action.setEnabled(enabled)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def _build_menus(self):
        bar = self.menuBar()
        media = bar.addMenu("Media")
        self._action(media, "Open file...", self.open_file)
        self._action(media, "Open folder...", enabled=False)
        self._action(media, "Open URL...", enabled=False)
        media.addSeparator()
        self._action(media, "Download posters and covers", enabled=False)
        media.addSeparator()
        recent = media.addMenu("Recent")
        self._action(recent, "No recent files", enabled=False)
        self._action(media, "Clear recent", enabled=False)

        playback = bar.addMenu("Playback")
        self._action(playback, "Play / Pause", self.toggle_pause, shortcut="Space")
        self._action(playback, "Stop", self.engine.stop)
        playback.addSeparator()
        timer = playback.addMenu("Sleep timer")
        for minutes in (15, 30, 45, 60, 90):
            self._action(timer, f"{minutes} minutes", enabled=False)
        self._action(timer, "Cancel sleep timer", enabled=False)
        playback.addSeparator()
        self._action(playback, "Back 10 s", lambda: self.seek(-10))
        self._action(playback, "Forward 10 s", lambda: self.seek(10))
        playback.addSeparator()
        self._action(playback, "Set A (loop start)", enabled=False)
        self._action(playback, "Set B (loop end)", enabled=False)
        self._action(playback, "Clear A-B loop", enabled=False)
        playback.addSeparator()
        self._action(playback, "Previous", enabled=False)
        self._action(playback, "Next", enabled=False)
        playback.addSeparator()
        self._action(playback, "Shuffle", enabled=False)
        repeat = playback.addMenu("Repeat")
        for label in ("No repeat", "Repeat one", "Repeat all"):
            self._action(repeat, label, enabled=False)
        self._action(playback, "Chapters", enabled=False)
        for speed in ("0.5", "0.75", "1", "1.25", "1.5", "2"):
            self._action(playback, f"Speed x{speed}", enabled=False)

        video = bar.addMenu("Video")
        for label in ("Aspect Auto", "Aspect 16:9", "Aspect 4:3", "Aspect 21:9",
                      "Fill screen (crop)", "Deinterlace", "Hardware decoding",
                      "Brightness +", "Brightness -", "Contrast +", "Contrast -",
                      "Saturation +", "Saturation -", "Reset picture", "Screenshot"):
            self._action(video, label, enabled=False)
            if label == "Aspect 21:9" or label == "Hardware decoding" or label == "Reset picture":
                video.addSeparator()

        audio = bar.addMenu("Audio")
        self._action(audio, "Audio tracks", enabled=False)
        self._action(audio, "Subtitles off", enabled=False)
        self._action(audio, "Load subtitles...", enabled=False)
        self._action(audio, "Search subtitles online...", enabled=False)
        for label in ("Subtitle delay +100 ms", "Subtitle delay -100 ms",
                      "Subtitles larger", "Subtitles smaller", "Reset subtitles"):
            self._action(audio, label, enabled=False)
        audio.addSeparator()
        for label in ("Volume boost +50%", "Normalize loudness",
                      "Audio output device...", "Audio equalizer...",
                      "Delay +100 ms", "Delay -100 ms", "Reset delay"):
            self._action(audio, label, enabled=False)

        iptv = bar.addMenu("IPTV")
        for label in ("Playlists", "Add playlist URL", "Open playlists folder",
                      "Reload playlists"):
            self._action(iptv, label, enabled=False)
        iptv.addSeparator()
        for label in ("TV guide", "Programme guide", "Add guide URL", "Reload guide"):
            self._action(iptv, label, enabled=False)
        iptv.addSeparator()
        for label in ("Recording", "Record now", "Schedule...",
                      "Cancel schedule", "Open recordings folder"):
            self._action(iptv, label, enabled=False)

        view = bar.addMenu("View")
        self._action(view, "Fullscreen", self.toggle_fullscreen)
        self._action(view, "Picture in picture", enabled=False)
        self._action(view, "Split screen  F2", enabled=False)
        self._action(view, "Always on top", enabled=False)
        view.addSeparator()
        self._action(view, "Hide list", self.toggle_left_panel)
        self._action(view, "Hide sidebar", self.toggle_right_panel)
        view.addSeparator()
        language = view.addMenu("Language")
        for label in ("English", "Italiano", "Español", "Français", "Deutsch",
                      "Português", "Русский"):
            self._action(language, label, enabled=False)
        view.addSeparator()
        buffer_menu = view.addMenu("Buffer")
        for label in ("Minimal", "Low", "Standard", "High"):
            self._action(buffer_menu, label, enabled=False)

        help_menu = bar.addMenu("Help")
        self._action(help_menu, "About XVB...", enabled=False)
        help_menu.addSeparator()
        self._action(help_menu, "Check for updates", enabled=False)
        self._action(help_menu, "Up to date", enabled=False)
        help_menu.addSeparator()
        self._action(help_menu, "Donate", enabled=False)

    def _build_layout(self):
        root = QWidget(self)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 10, 8, 8)
        left_layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        left_layout.addWidget(self.search)
        self.media_tree = QTreeWidget()
        self.media_tree.setHeaderHidden(True)
        self.media_tree.setIndentation(16)
        self.media_tree.setAlternatingRowColors(False)
        left_layout.addWidget(self.media_tree, 1)

        self.video = MPVRenderWidget(self.engine, self)
        self.video.setMinimumSize(320, 180)
        self.video.setStyleSheet("background: #000000;")

        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(220)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(8, 10, 8, 8)
        right_layout.setSpacing(5)
        playlists_label = QLabel("Playlists")
        playlists_label.setStyleSheet(f"color: {GRIGIO}; padding: 0 2px 3px 2px;")
        right_layout.addWidget(playlists_label)
        self.playlist_tree = QTreeWidget()
        self.playlist_tree.setHeaderHidden(True)
        self.playlist_tree.setIndentation(14)
        self.playlist_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        right_layout.addWidget(self.playlist_tree, 1)

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.video)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 760, 220])
        outer.addWidget(splitter, 1)

        self.notification = QFrame()
        self.notification.setFixedHeight(42)
        self.notification.setStyleSheet(f"background: {IN_ONDA2};")
        notice_layout = QHBoxLayout(self.notification)
        notice_layout.setContentsMargins(12, 0, 10, 0)
        notice_title = QLabel("xvb")
        notice_title.setStyleSheet(f"color: {ACCENTO}; font-size: 13pt; font-weight: bold;")
        notice_layout.addWidget(notice_title)
        self.notice_text = QLabel("")
        self.notice_text.setStyleSheet(f"color: {TESTO_ONDA};")
        notice_layout.addWidget(self.notice_text, 1)
        self.notification.hide()
        outer.addWidget(self.notification)

        self.control_bar = QFrame()
        self.control_bar.setFixedHeight(96)
        controls = QHBoxLayout(self.control_bar)
        controls.setContentsMargins(8, 5, 8, 5)
        controls.setSpacing(2)

        self.playlist_button = self._tool_button("playlist", "Playlists", self.toggle_right_panel)
        controls.addWidget(self.playlist_button)
        controls.addSpacing(12)
        controls.addWidget(self._tool_button("prima", "Previous", enabled=False))
        controls.addWidget(self._text_button("-10", "Back 10 seconds", lambda: self.seek(-10)))
        self.play_button = self._tool_button("play", "Play", self.toggle_pause)
        controls.addWidget(self.play_button)
        controls.addWidget(self._tool_button("stop", "Stop", self.engine.stop))
        controls.addWidget(self._text_button("+10", "Forward 10 seconds", lambda: self.seek(10)))
        controls.addWidget(self._tool_button("dopo", "Next", enabled=False))
        controls.addSpacing(14)
        controls.addWidget(self._tool_button("rec", "Record", enabled=False))
        controls.addWidget(self._tool_button("repeat", "No repeat", enabled=False))
        controls.addWidget(self._tool_button("shuffle", "Shuffle", enabled=False))
        controls.addStretch(1)
        controls.addWidget(self._tool_button("favorite_off", "Favorite", enabled=False))
        controls.addWidget(self._tool_button("pieno", "Fullscreen", self.toggle_fullscreen))
        controls.addWidget(self._tool_button("pip", "Picture in picture", enabled=False))
        controls.addWidget(self._tool_button("setting", "Quality", enabled=False))
        self.volume_button = self._tool_button("volume", "Mute", self.toggle_mute)
        controls.addWidget(self.volume_button)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(85)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls.addWidget(self.volume_slider)
        outer.addWidget(self.control_bar)

        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(f"background: {STATO};")
        status = QHBoxLayout(self.status_bar)
        status.setContentsMargins(8, 0, 10, 0)
        status.setSpacing(7)
        self.category_status = QLabel("")
        self.playback_status = QLabel("ready")
        self.title_status = QLabel("")
        self.program_time_status = QLabel("")
        self.next_status = QLabel("")
        self.format_status = QLabel("")
        for widget in (self.category_status, self.playback_status, self.title_status,
                       self.program_time_status, self.next_status, self.format_status):
            widget.setStyleSheet(f"background: {STATO}; color: {TESTO};")
            status.addWidget(widget)
        status.addStretch(1)
        self.clock_status = QLabel("")
        self.clock_status.setStyleSheet(f"background: {STATO}; color: {TESTO};")
        status.addWidget(self.clock_status)
        outer.addWidget(self.status_bar)
        self.setCentralWidget(root)

    def _tool_button(self, icon_name, tooltip, callback=None, enabled=True):
        button = QToolButton()
        button.setToolTip(tooltip)
        button.setIcon(self._icon(icon_name))
        button.setIconSize(self._icon_size(icon_name))
        button.setFixedSize(42, 42)
        button.setEnabled(enabled)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        if callback is not None:
            button.clicked.connect(callback)
        return button

    def _text_button(self, text, tooltip, callback):
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(48, 40)
        button.clicked.connect(callback)
        return button

    def _icon_size(self, name):
        if name == "stop":
            return self._size(24, 24)
        return self._size(34, 30)

    def _size(self, width, height):
        from PySide6.QtCore import QSize
        return QSize(width, height)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file")
        if path:
            self.engine.load(path)
            self.title_status.setText(Path(path).name)

    def toggle_pause(self):
        self.engine.command("cycle", "pause")

    def seek(self, seconds):
        self.engine.command("seek", str(seconds), "relative")

    def set_volume(self, value):
        self.engine.command("set_property", "volume", str(value))

    def toggle_mute(self):
        self.engine.command("cycle", "mute")

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def toggle_left_panel(self):
        self.left_panel.setVisible(not self.left_panel.isVisible())

    def toggle_right_panel(self):
        self.right_panel.setVisible(not self.right_panel.isVisible())

    def _update_clock(self):
        self.clock_status.setText(QDateTime.currentDateTime().toString("ddd dd MMM  HH:mm"))

    def closeEvent(self, event):
        self.video.close_render_context()
        self.engine.close()
        super().closeEvent(event)
