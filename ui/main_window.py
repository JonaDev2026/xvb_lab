import hashlib
import random
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QDateTime, QThread, QObject, Signal, QSize
from PySide6.QtGui import QAction, QActionGroup, QBrush, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
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
from features.sleep_timer import SleepTimer
from ui.metrics import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    LEFT_PANEL_WIDTH, RIGHT_PANEL_WIDTH, MEDIA_ROW_HEIGHT,
    MEDIA_LOGO_WIDTH, MEDIA_LOGO_HEIGHT, PLAYLIST_ROW_HEIGHT,
    STATUS_BAR_HEIGHT, STATUS_FONT_PX, CONTROL_BAR_HEIGHT,
    NOTIFICATION_BAR_HEIGHT,
)
from core.config import load_config, save_config
from features.local_media import iter_folder_batches, scan_imported, load_tag_cache, save_tag_cache, read_media_tags, cache_cover_art


class FolderScanWorker(QObject):
    batch_ready = Signal(object, str, object, int)
    finished = Signal(object, object, str, object, int)

    def __init__(self, source, value, token):
        super().__init__()
        self.source = source
        self.value = value
        self.token = token

    def run(self):
        try:
            items = []
            if self.source == "folder":
                batches = iter_folder_batches(self.value)
            else:
                imported = scan_imported(self.value)
                batches = (imported[index:index + 30] for index in range(0, len(imported), 30))
            for batch in batches:
                if QThread.currentThread().isInterruptionRequested():
                    break
                items.extend(batch)
                self.batch_ready.emit(batch, self.source, self.value, self.token)
            self.finished.emit(items, None, self.source, self.value, self.token)
        except Exception as error:
            self.finished.emit([], str(error), self.source, self.value, self.token)


class MetadataWorker(QObject):
    finished = Signal(object, str, str, object, int)

    def __init__(self, items, source, value, token):
        super().__init__()
        self.items = items
        self.source = source
        self.value = value
        self.token = token

    def run(self):
        try:
            cache = load_tag_cache()
            changed = False
            metadata = {}
            for media in self.items:
                if QThread.currentThread().isInterruptionRequested():
                    break
                if media["kind"] != "music":
                    continue
                path = media["path"]
                previous = cache.get(path)
                tags = read_media_tags(path, cache)
                metadata[path] = (tags, cache_cover_art(path))
                if cache.get(path) != previous:
                    changed = True
            if changed:
                save_tag_cache(cache)
            self.finished.emit(metadata, "", self.source, self.value, self.token)
        except Exception as error:
            self.finished.emit({}, str(error), self.source, self.value, self.token)


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
        self.config = load_config()
        self.config.setdefault("folders", [])
        self.config.setdefault("imported", [])
        self.config.setdefault("recent", [])
        self.config.setdefault("volume", 100)
        self.config.setdefault("muted", False)
        self.config.setdefault("shuffle", False)
        self.config.setdefault("repeat", "")
        self._scan_threads = []
        self._metadata_threads = []
        self._media_tree_items = {}
        self._current_media_path = None
        self._end_handled = False
        self._seen_playback = False
        self._normal_media_order = []
        self.previous_button = None
        self.next_button = None
        self._vinyl_icons = {}
        self.sleep_timer = SleepTimer(self)
        self.sleep_timer.expired.connect(self._sleep_timer_expired)
        self.resource_dir = Path(__file__).resolve().parents[1] / "resources"
        self.icons_dir = self.resource_dir / "icons"
        self.setWindowTitle("XVB v4.4.4")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
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
        repeat_mode = self.config.get("repeat", "")
        self.repeat_button.setIcon(self._icon("repeat_one" if repeat_mode == "one" else "repeat"))
        self.repeat_button.setToolTip({"": "No repeat", "one": "Repeat one", "all": "Repeat all"}.get(repeat_mode, "No repeat"))
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start(1000)
        self._update_clock()
        self._end_timer = QTimer(self)
        self._end_timer.timeout.connect(self._check_playback_end)
        self._end_timer.timeout.connect(self._update_playback_display)
        self._end_timer.start(500)
        self.engine.command("set", "volume", str(self.volume_slider.value()))
        self.engine.command("set", "mute", "yes" if self.config.get("muted", False) else "no")

    def _icon(self, name):
        path = self.icons_dir / f"{name}.png"
        return QIcon(str(path)) if path.is_file() else QIcon()

    def _vinyl_icon(self, name):
        colors = ("#ff5257", "#ff9f0a", "#ffd60a", "#30d158", "#0a84ff", "#bf5af2", "#ff375f", "#64d2ff")
        digest = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16)
        color = colors[digest % len(colors)]
        if color in self._vinyl_icons:
            return self._vinyl_icons[color]
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#6a6a74"), 1))
        painter.setBrush(QColor(24, 24, 28))
        painter.drawEllipse(1, 1, 22, 22)
        painter.setPen(QPen(QColor(72, 72, 80), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(4, 4, 16, 16)
        painter.drawEllipse(6, 6, 12, 12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawEllipse(7, 7, 10, 10)
        painter.setBrush(QColor(24, 24, 28))
        painter.drawEllipse(10.2, 10.2, 3.6, 3.6)
        painter.end()
        icon = QIcon(pixmap)
        self._vinyl_icons[color] = icon
        return icon

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
        self._action(media, "Open folder...", self.open_folder)
        self._action(media, "Open URL...", self.open_url)
        media.addSeparator()
        self._action(media, "Download posters and covers", enabled=False)
        media.addSeparator()
        self.recent_menu = media.addMenu("Recent")
        self.recent_menu.aboutToShow.connect(self._populate_recent_menu)
        self._action(media, "Clear recent", self.clear_recent)

        playback = bar.addMenu("Playback")
        self._action(playback, "Play / Pause", self.toggle_pause, shortcut="Space")
        self._action(playback, "Stop", self.stop_playback, shortcut="Ctrl+.")
        self._action(playback, "Previous", self.play_previous, shortcut="Ctrl+Left")
        self._action(playback, "Next", self.play_next, shortcut="Ctrl+Right")
        playback.addSeparator()
        self._action(playback, "Sleep timer", enabled=False)
        for minutes in (15, 30, 45, 60, 90):
            self._action(playback, f"{minutes} minutes", lambda checked=False, value=minutes: self.set_sleep_timer(value))
        self._action(playback, "Cancel sleep timer", self.cancel_sleep_timer)
        playback.addSeparator()
        self._action(playback, "Back 10 s", lambda: self.seek(-10), shortcut="Alt+Left")
        self._action(playback, "Forward 10 s", lambda: self.seek(10), shortcut="Alt+Right")
        playback.addSeparator()
        self._action(playback, "Set A (loop start)", enabled=False)
        self._action(playback, "Set B (loop end)", enabled=False)
        self._action(playback, "Clear A-B loop", enabled=False)
        playback.addSeparator()
        self._action(playback, "Previous", enabled=False)
        self._action(playback, "Next", enabled=False)
        playback.addSeparator()
        self.shuffle_action = self._action(playback, "Shuffle", self.toggle_shuffle)
        self.shuffle_action.setCheckable(True)
        self.shuffle_action.setChecked(bool(self.config.get("shuffle", False)))
        playback.addSeparator()
        repeat_group = QActionGroup(self)
        repeat_group.setExclusive(True)
        self.repeat_actions = {}
        for key, label in (("", "No repeat"), ("one", "Repeat one"), ("all", "Repeat all")):
            action = self._action(playback, label, lambda checked=False, mode=key: self.set_repeat(mode))
            action.setCheckable(True)
            repeat_group.addAction(action)
            self.repeat_actions[key] = action
        self.repeat_actions.get(self.config.get("repeat", ""), self.repeat_actions[""]).setChecked(True)
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
        self._action(view, "Fullscreen", self.toggle_fullscreen, shortcut="F11")
        self._action(view, "Picture in picture", enabled=False)
        self._action(view, "Split screen  F2", enabled=False)
        self._action(view, "Always on top", enabled=False)
        view.addSeparator()
        self.left_toggle_action = self._action(view, "Hide list", self.toggle_left_panel)
        self.right_toggle_action = self._action(view, "Hide sidebar", self.toggle_right_panel)
        view.addSeparator()
        self._action(view, "Language", enabled=False)
        for label in ("English", "Italiano", "Español", "Français", "Deutsch",
                      "Português", "Русский"):
            self._action(view, label, enabled=False)
        view.addSeparator()
        self._action(view, "Buffer", enabled=False)
        for label in ("Minimal", "Low", "Standard", "High"):
            self._action(view, label, enabled=False)

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
        self.left_panel.setMinimumWidth(LEFT_PANEL_WIDTH)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 10, 8, 8)
        left_layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        left_layout.addWidget(self.search)
        self.media_tree = QTreeWidget()
        self.media_tree.setHeaderHidden(True)
        self.media_tree.setIconSize(QSize(MEDIA_LOGO_WIDTH, MEDIA_LOGO_HEIGHT))
        self.media_tree.setStyleSheet(f"QTreeWidget::item {{ height: {MEDIA_ROW_HEIGHT}px; }}")
        self.media_tree.setIndentation(16)
        self.media_tree.setAlternatingRowColors(False)
        self.media_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.media_tree.customContextMenuRequested.connect(self.media_context_menu)
        self.media_tree.itemDoubleClicked.connect(self.play_selected_media)
        self.search.textChanged.connect(self.filter_media)
        left_layout.addWidget(self.media_tree, 1)

        self.video = MPVRenderWidget(self.engine, self)
        self.video.setMinimumSize(320, 180)
        self.video.setStyleSheet("background: #000000;")

        self.right_panel = QFrame()
        self.right_panel.setMinimumWidth(RIGHT_PANEL_WIDTH)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(8, 10, 8, 8)
        right_layout.setSpacing(5)
        playlists_label = QLabel("Playlists")
        playlists_label.setStyleSheet(f"color: {GRIGIO}; padding: 0 2px 3px 2px;")
        right_layout.addWidget(playlists_label)
        self.playlist_tree = QTreeWidget()
        self.playlist_tree.setHeaderHidden(True)
        self.playlist_tree.setIndentation(14)
        self.playlist_tree.setStyleSheet(f"QTreeWidget::item {{ height: {PLAYLIST_ROW_HEIGHT}px; }}")
        self.playlist_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.playlist_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_tree.customContextMenuRequested.connect(self.local_tree_context_menu)
        self.playlist_tree.itemClicked.connect(self.select_local_source)
        self.playlist_tree.itemExpanded.connect(self._tree_expansion_changed)
        self.playlist_tree.itemCollapsed.connect(self._tree_expansion_changed)
        right_layout.addWidget(self.playlist_tree, 1)
        self._populate_local_tree()

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.video)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 760, 220])
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        self.notification = QFrame()
        self.notification.setFixedHeight(NOTIFICATION_BAR_HEIGHT)
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
        self.control_bar.setFixedHeight(CONTROL_BAR_HEIGHT)
        controls = QHBoxLayout(self.control_bar)
        controls.setContentsMargins(8, 5, 8, 5)
        controls.setSpacing(2)

        controls.addSpacing(12)
        self.previous_button = self._tool_button("prima", "Previous", self.play_previous, enabled=False)
        controls.addWidget(self.previous_button)
        controls.addWidget(self._text_button("-10", "Back 10 seconds", lambda: self.seek(-10)))
        self.play_button = self._tool_button("play", "Play / Pause", self.toggle_pause)
        controls.addWidget(self.play_button)
        controls.addWidget(self._tool_button("stop", "Stop", self.stop_playback))
        controls.addWidget(self._text_button("+10", "Forward 10 seconds", lambda: self.seek(10)))
        self.next_button = self._tool_button("dopo", "Next", self.play_next, enabled=False)
        controls.addWidget(self.next_button)
        controls.addSpacing(8)
        self.repeat_button = self._tool_button("repeat", "No repeat", self.cycle_repeat)
        controls.addWidget(self.repeat_button)
        self.shuffle_button = self._tool_button("shuffle", "Shuffle off", self.toggle_shuffle)
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setChecked(bool(self.config.get("shuffle", False)))
        controls.addWidget(self.shuffle_button)
        controls.addWidget(self._tool_button("rec", "Record", enabled=False))
        controls.addSpacing(8)
        self.position_label = QLabel("00:00")
        self.position_label.setMinimumWidth(42)
        controls.addWidget(self.position_label)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setMinimumWidth(100)
        self.position_slider.setTracking(False)
        self.position_slider.sliderPressed.connect(self._position_pressed)
        self.position_slider.sliderReleased.connect(self._position_released)
        controls.addWidget(self.position_slider, 1)
        self.duration_label = QLabel("00:00")
        self.duration_label.setMinimumWidth(42)
        controls.addWidget(self.duration_label)
        self.favorite_button = self._tool_button("favorite_off", "Favorite", enabled=False)
        self.favorite_button.hide()
        controls.addWidget(self.favorite_button)
        self.playlist_button = self._tool_button("playlist", "Playlists", self.toggle_right_panel)
        controls.addWidget(self.playlist_button)
        controls.addWidget(self._tool_button("pieno", "Fullscreen", self.toggle_fullscreen))
        controls.addWidget(self._tool_button("pip", "Picture in picture", enabled=False))
        self.quality_button = self._tool_button("setting", "Quality", enabled=False)
        self.quality_button.hide()
        controls.addWidget(self.quality_button)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(max(0, min(100, int(self.config.get("volume", 100)))))
        self.volume_slider.setFixedWidth(85)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.sliderReleased.connect(self._save_volume)
        controls.addWidget(self.volume_slider)
        muted = bool(self.config.get("muted", False))
        self.volume_button = self._tool_button("volume_off" if muted else "volume", "Unmute" if muted else "Mute", self.toggle_mute)
        controls.addWidget(self.volume_button)
        outer.addWidget(self.control_bar)

        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(STATUS_BAR_HEIGHT)
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
            widget.setStyleSheet(f"background: {STATO}; color: {TESTO}; font-size: {STATUS_FONT_PX}px;")
            status.addWidget(widget)
        status.addStretch(1)
        self.clock_status = QLabel("")
        self.clock_status.setStyleSheet(f"background: {STATO}; color: {TESTO}; font-size: {STATUS_FONT_PX}px;")
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
        return self._size(34, 34)

    def _size(self, width, height):
        from PySide6.QtCore import QSize
        return QSize(width, height)

    def _tree_expansion_changed(self, item):
        key = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if key:
            self.config.setdefault("expanded", {})[key] = item.isExpanded()
            save_config(self.config)

    def _set_tree_expanded(self, item, key, default=False):
        item.setData(0, Qt.ItemDataRole.UserRole + 1, key)
        item.setExpanded(bool(self.config.get("expanded", {}).get(key, default)))

    def _populate_local_tree(self):
        self.playlist_tree.blockSignals(True)
        self.playlist_tree.clear()
        self._source_tree_items = {}
        root = QTreeWidgetItem(["Local"])
        root.setIcon(0, self._icon("player"))
        self.playlist_tree.addTopLevelItem(root)
        for folder in self.config.get("folders", []):
            path = Path(folder).expanduser()
            if not path.is_dir():
                continue
            item = QTreeWidgetItem([path.name or str(path)])
            item.setData(0, Qt.ItemDataRole.UserRole, ("folder", str(path.resolve())))
            item.setIcon(0, self._icon("player"))
            root.addChild(item)
            self._set_tree_expanded(item, "folder:" + str(path.resolve()))
            self._source_tree_items[("folder", str(path.resolve()))] = item
        imported = [str(Path(path).expanduser().resolve()) for path in self.config.get("imported", [])
                    if Path(path).expanduser().is_file()]
        if imported:
            item = QTreeWidgetItem([f"Imported media ({len(imported)})"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("imported", imported))
            item.setIcon(0, self._icon("playlist"))
            root.addChild(item)
            self._source_tree_items[("imported", tuple(imported))] = item
            self._set_tree_expanded(item, "imported")
            for path in imported:
                child = QTreeWidgetItem([Path(path).stem])
                child.setData(0, Qt.ItemDataRole.UserRole, ("imported", [path]))
                child.setIcon(0, self._icon("music" if Path(path).suffix.lower().lstrip(".") in {
                    "aac", "aif", "aiff", "alac", "ape", "flac", "m4a", "m4b", "m4p",
                    "mid", "midi", "mp3", "mpc", "oga", "ogg", "opus", "wav", "wma", "wv"
                } else "player"))
                item.addChild(child)
                self._source_tree_items[("imported", (path,))] = child
        self._set_tree_expanded(root, "local", True)
        self.playlist_tree.blockSignals(False)

    def local_tree_context_menu(self, position):
        item = self.playlist_tree.itemAt(position)
        if item is None:
            return
        source = item.data(0, Qt.ItemDataRole.UserRole)
        if not source:
            return
        kind, value = source
        menu = QMenu(self)
        if kind == "folder":
            action = menu.addAction("Remove folder from list")
            chosen = menu.exec(self.playlist_tree.viewport().mapToGlobal(position))
            if chosen == action:
                self.remove_local_source(item)
            return
        if kind == "imported":
            paths = list(value) if isinstance(value, (list, tuple)) else [value]
            if len(paths) == 1:
                action = menu.addAction("Remove file from list")
            else:
                action = menu.addAction("Remove imported media")
            chosen = menu.exec(self.playlist_tree.viewport().mapToGlobal(position))
            if chosen == action:
                self.remove_local_source(item)
            return

    def remove_local_source(self, item):
        source = item.data(0, Qt.ItemDataRole.UserRole)
        if not source:
            return
        kind, value = source
        if kind == "folder":
            answer = QMessageBox.question(
                self,
                "Remove folder",
                "The folder will be removed from the list. Files on disk will not be touched.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            folder = str(Path(value).resolve())
            self.config["folders"] = [
                path for path in self.config.get("folders", [])
                if str(Path(path).expanduser().resolve()) != folder
            ]
        elif kind == "imported":
            paths = list(value) if isinstance(value, (list, tuple)) else [value]
            if len(paths) == 1:
                answer = QMessageBox.question(
                    self,
                    "Remove imported file",
                    "The file will be removed from the list. The file on disk will not be touched.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
                target = str(Path(paths[0]).expanduser().resolve())
                self.config["imported"] = [
                    path for path in self.config.get("imported", [])
                    if str(Path(path).expanduser().resolve()) != target
                ]
            else:
                answer = QMessageBox.question(
                    self,
                    "Remove imported media",
                    "All imported files will be removed from the list. Files on disk will not be touched.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
                self.config["imported"] = []
        else:
            return
        save_config(self.config)
        self._scan_token = getattr(self, "_scan_token", 0) + 1
        self._active_source = None
        self.media_tree.clear()
        self.title_status.setText("")
        self.playback_status.setText("ready")
        self._populate_local_tree()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open folder")
        if not folder:
            return
        folder = str(Path(folder).resolve())
        if folder not in self.config["folders"]:
            self.config["folders"].append(folder)
            save_config(self.config)
        self._populate_local_tree()
        self._scan_source("folder", folder)

    def select_local_source(self, item, _column):
        source = item.data(0, Qt.ItemDataRole.UserRole)
        if source:
            self._update_local_selection(source)
            self._scan_source(source[0], source[1])

    def _update_local_selection(self, source):
        active = (source[0], tuple(source[1]) if source[0] == "imported" else str(source[1]))
        for key, item in getattr(self, "_source_tree_items", {}).items():
            current = (key[0], tuple(key[1]) if key[0] == "imported" else str(key[1]))
            if current == active:
                item.setBackground(0, QColor(IN_ONDA))
                item.setForeground(0, QColor(TESTO_ONDA))
            else:
                item.setBackground(0, QBrush())
                item.setForeground(0, QBrush())

    def _scan_source(self, source, value):
        for previous in self._scan_threads + self._metadata_threads:
            previous.requestInterruption()
        self._scan_token = getattr(self, "_scan_token", 0) + 1
        token = self._scan_token
        self._active_source = (source, value)
        self._current_media_path = None
        self._update_playback_navigation()
        self._update_local_selection((source, value))
        self.media_tree.clear()
        self._media_tree_items = {}
        self.notification.hide()
        self.playback_status.setText("Loading...")
        thread = QThread(self)
        worker = FolderScanWorker(source, value, token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.batch_ready.connect(self._append_media_batch)
        worker.finished.connect(self._show_media_items)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._scan_threads.remove(thread) if thread in self._scan_threads else None)
        self._scan_threads.append(thread)
        thread.start()

    def _append_media_batch(self, items, source, value, token):
        if getattr(self, "_closing", False):
            return
        if token != getattr(self, "_scan_token", None):
            return
        if getattr(self, "_active_source", None) != (source, value):
            return
        for media in items:
            item = QTreeWidgetItem([media["name"]])
            item.setData(0, Qt.ItemDataRole.UserRole, media["path"])
            item.setIcon(0, self._icon("music" if media["kind"] == "music" else "player"))
            query = self.search.text().casefold().strip()
            item.setHidden(bool(query) and query not in media["name"].casefold())
            self.media_tree.addTopLevelItem(item)
            self._media_tree_items[media["path"]] = item
        self._update_playback_navigation()

    def _show_media_items(self, items, error, source, value, token):
        if getattr(self, "_closing", False):
            return
        if token != getattr(self, "_scan_token", None):
            return
        if getattr(self, "_active_source", None) != (source, value):
            return
        if error:
            self.playback_status.setText("Library error")
            self.notice_text.setText(error)
            self.notification.show()
            return
        source, value = getattr(self, "_active_source", (None, None))
        if source == "folder":
            root_path = Path(value).resolve()
            source_item = getattr(self, "_source_tree_items", {}).get(("folder", str(root_path)))
            if source_item is not None:
                total = len(items)
                source_item.setText(0, f"{root_path.name or str(root_path)} ({total})")
                music_count = sum(media["kind"] == "music" for media in items)
                parent_is_music = bool(items) and music_count * 2 > total
                source_item.setIcon(0, self._icon("music" if parent_is_music else "player"))
                for key in list(self._source_tree_items):
                    if key[0] != "folder" or key[1] == str(root_path):
                        continue
                    try:
                        Path(key[1]).relative_to(root_path)
                        self._source_tree_items.pop(key, None)
                    except ValueError:
                        pass
                source_item.takeChildren()
                groups = {}
                for media in items:
                    try:
                        relative = Path(media["path"]).resolve().relative_to(root_path)
                    except (ValueError, OSError):
                        continue
                    if len(relative.parts) > 1:
                        groups.setdefault(relative.parts[0], []).append(media)
                for dirname, children in sorted(groups.items(), key=lambda pair: pair[0].casefold()):
                    child_path = root_path / dirname
                    child = QTreeWidgetItem([f"{dirname} ({len(children)})"])
                    child.setData(0, Qt.ItemDataRole.UserRole, ("folder", str(child_path)))
                    music_count = sum(media["kind"] == "music" for media in children)
                    if parent_is_music:
                        child.setIcon(0, self._vinyl_icon(dirname))
                    else:
                        icon = "music" if music_count * 2 > len(children) else "player"
                        child.setIcon(0, self._icon(icon))
                    source_item.addChild(child)
                    self._set_tree_expanded(child, "folder:" + str(child_path.resolve()))
                    self._source_tree_items[("folder", str(child_path.resolve()))] = child
                source_key = "folder:" + str(root_path)
                source_item.setData(0, Qt.ItemDataRole.UserRole + 1, source_key)
                source_item.setExpanded(bool(self.config.get("expanded", {}).get(source_key, False)))
        elif source == "imported":
            paths = tuple(value) if isinstance(value, (list, tuple)) else (str(value),)
            source_item = self._source_tree_items.get(("imported", paths))
            if source_item is not None:
                label = source_item.text(0).split(" (")[0]
                source_item.setText(0, f"{label} ({len(items)})")
        self.playback_status.setText(f"{len(items)} files")
        thread = QThread(self)
        worker = MetadataWorker(items, source, value, token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._apply_media_metadata)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._metadata_threads.remove(thread) if thread in self._metadata_threads else None)
        self._metadata_threads.append(thread)
        thread.start()

    def _apply_media_metadata(self, metadata, error, source, value, token):
        if getattr(self, "_closing", False):
            return
        if token != getattr(self, "_scan_token", None):
            return
        if getattr(self, "_active_source", None) != (source, value) or error:
            return
        for path, result in metadata.items():
            item = self._media_tree_items.get(path)
            if item is None:
                continue
            tags, cover_path = result
            title, artist, album, year = tags
            if cover_path:
                pixmap = QPixmap(cover_path)
                if not pixmap.isNull():
                    item.setIcon(0, QIcon(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            subtitle = " · ".join(part for part in (artist, album, year) if part)
            item.setText(0, title or Path(path).stem)
            if subtitle:
                item.setText(0, item.text(0) + "\n" + subtitle)
                item.setSizeHint(0, QSize(0, 42))
            item.setToolTip(0, path)
            query = self.search.text().casefold().strip()
            item.setHidden(bool(query) and query not in item.text(0).casefold())
        self.media_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        self._normal_media_order = [self.media_tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) for i in range(self.media_tree.topLevelItemCount())]
        if self.config.get("shuffle"):
            self._apply_shuffle()
        self._update_playback_navigation()

    def media_context_menu(self, position):
        item = self.media_tree.itemAt(position)
        if item is None:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or not Path(path).is_file():
            return
        menu = QMenu(self)
        set_cover = menu.addAction("Set cover...")
        cover_files = [Path(path).with_suffix(ext) for ext in (".jpg", ".jpeg", ".png")]
        existing = next((cover for cover in cover_files if cover.is_file()), None)
        remove_cover = menu.addAction("Remove cover") if existing else None
        chosen = menu.exec(self.media_tree.viewport().mapToGlobal(position))
        if chosen == set_cover:
            image, _ = QFileDialog.getOpenFileName(
                self, "Choose cover", str(Path(path).parent),
                "Images (*.jpg *.jpeg *.png *.webp)"
            )
            if image:
                source = Path(image)
                destination = Path(path).with_suffix(source.suffix.lower())
                try:
                    for cover in cover_files:
                        if cover != destination and cover.exists():
                            cover.unlink()
                    shutil.copyfile(source, destination)
                    self._refresh_media_cover(path)
                except OSError as error:
                    QMessageBox.warning(self, "Cover", str(error))
        elif remove_cover is not None and chosen == remove_cover:
            try:
                existing.unlink()
                self._refresh_media_cover(path)
            except OSError as error:
                QMessageBox.warning(self, "Cover", str(error))

    def _refresh_media_cover(self, path):
        item = self._media_tree_items.get(path)
        if item is None:
            return
        cover_path = cache_cover_art(path)
        if cover_path:
            pixmap = QPixmap(cover_path)
            if not pixmap.isNull():
                item.setIcon(0, QIcon(pixmap.scaled(
                    48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )))
        else:
            item.setIcon(0, self._icon("music"))

    def filter_media(self, text):
        query = text.casefold().strip()
        for index in range(self.media_tree.topLevelItemCount()):
            item = self.media_tree.topLevelItem(index)
            item.setHidden(bool(query) and query not in item.text(0).casefold())
        self._update_playback_navigation()

    def play_selected_media(self, item, _column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self._play_media_path(path)

    def _play_media_path(self, path):
        if not path or not Path(path).is_file():
            return
        self._end_handled = False
        self._seen_playback = False
        self.engine.load(path)
        self._current_media_path = str(path)
        self._add_recent(str(path))
        self.title_status.setText(Path(path).name)
        self.playback_status.setText("playing")
        self._update_playback_navigation()

    def _visible_media_paths(self):
        paths = []
        for index in range(self.media_tree.topLevelItemCount()):
            item = self.media_tree.topLevelItem(index)
            if item.isHidden():
                continue
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(str(path))
        return paths

    def _update_playback_navigation(self):
        paths = self._visible_media_paths()
        try:
            index = paths.index(self._current_media_path)
        except ValueError:
            index = -1
        if self.previous_button is not None:
            self.previous_button.setEnabled(index > 0)
        if self.next_button is not None:
            self.next_button.setEnabled(0 <= index < len(paths) - 1)

    def _play_adjacent_media(self, offset, wrap=False):
        paths = self._visible_media_paths()
        try:
            index = paths.index(self._current_media_path)
        except ValueError:
            return
        target = index + offset
        if wrap and paths:
            target %= len(paths)
        if 0 <= target < len(paths):
            self._play_media_path(paths[target])

    def _apply_shuffle(self):
        paths = self._visible_media_paths()
        if not paths:
            return
        current = self._current_media_path
        random.shuffle(paths)
        if current in paths:
            paths.remove(current)
            paths.insert(0, current)
        items = {}
        for index in range(self.media_tree.topLevelItemCount()):
            item = self.media_tree.topLevelItem(index)
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                items[str(path)] = item
        self.media_tree.setSortingEnabled(False)
        for index in range(self.media_tree.topLevelItemCount() - 1, -1, -1):
            self.media_tree.takeTopLevelItem(index)
        for path in paths:
            if path in items:
                self.media_tree.addTopLevelItem(items.pop(path))
        for item in items.values():
            self.media_tree.addTopLevelItem(item)
        self._update_playback_navigation()

    def toggle_shuffle(self):
        enabled = not bool(self.config.get("shuffle", False))
        self.config["shuffle"] = enabled
        self.shuffle_action.setChecked(enabled)
        self.shuffle_button.setChecked(enabled)
        self.shuffle_button.setIcon(self._icon("shuffle"))
        self.shuffle_button.setToolTip("Shuffle on" if enabled else "Shuffle off")
        if enabled:
            self._apply_shuffle()
        elif self._normal_media_order:
            items = {}
            for index in range(self.media_tree.topLevelItemCount()):
                item = self.media_tree.topLevelItem(index)
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path:
                    items[str(path)] = item
            self.media_tree.setSortingEnabled(False)
            for index in range(self.media_tree.topLevelItemCount() - 1, -1, -1):
                self.media_tree.takeTopLevelItem(index)
            for path in self._normal_media_order:
                if path in items:
                    self.media_tree.addTopLevelItem(items.pop(path))
            for item in items.values():
                self.media_tree.addTopLevelItem(item)
            self._update_playback_navigation()
        save_config(self.config)

    def set_repeat(self, mode):
        self.config["repeat"] = mode
        self.repeat_actions[mode].setChecked(True)
        icon = "repeat_one" if mode == "one" else "repeat"
        self.repeat_button.setIcon(self._icon(icon))
        self.repeat_button.setToolTip({"": "No repeat", "one": "Repeat one", "all": "Repeat all"}[mode])
        save_config(self.config)

    def cycle_repeat(self):
        current = self.config.get("repeat", "")
        self.set_repeat({"": "all", "all": "one", "one": ""}.get(current, ""))

    def _position_pressed(self):
        self._seeking_position = True

    def _position_released(self):
        duration = self.engine.get_double("duration")
        if duration and duration > 0:
            target = duration * self.position_slider.value() / 1000
            self.engine.command("seek", f"{target:.3f}", "absolute")
        self._seeking_position = False

    def _format_time(self, seconds):
        if seconds is None or seconds < 0:
            return "--:--"
        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"

    def _update_playback_display(self):
        position = self.engine.get_double("time-pos")
        duration = self.engine.get_double("duration")
        self.position_label.setText(self._format_time(position))
        self.duration_label.setText(self._format_time(duration))
        if duration and duration > 0 and position is not None and not getattr(self, "_seeking_position", False):
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(max(0, min(1000, int(position / duration * 1000))))
            self.position_slider.blockSignals(False)
        try:
            paused = self.engine.get_flag("pause")
            self.play_button.setIcon(self._icon("play" if paused else "pausa"))
            self.play_button.setToolTip("Play" if paused else "Pause")
        except Exception:
            pass

    def _check_playback_end(self):
        if not self._current_media_path or self._end_handled:
            return
        eof = self.engine.get_flag("eof-reached")
        if not eof:
            self._seen_playback = True
            return
        if not self._seen_playback:
            return
        self._end_handled = True
        mode = self.config.get("repeat", "")
        if mode == "one":
            self._play_media_path(self._current_media_path)
        elif mode == "all":
            self._play_adjacent_media(1, wrap=True)
        else:
            self._current_media_path = None
            self.playback_status.setText("finished")
            self._update_playback_navigation()

    def play_previous(self):
        self._play_adjacent_media(-1)

    def play_next(self):
        self._play_adjacent_media(1)

    def open_url(self):
        url, accepted = QInputDialog.getText(self, "Open URL", "URL:")
        if not accepted or not url.strip():
            return
        url = url.strip()
        self.engine.load(url)
        self._current_media_path = None
        self.title_status.setText(url)
        self.playback_status.setText("playing")
        self._update_playback_navigation()

    def _add_recent(self, path):
        recent = [entry for entry in self.config.get("recent", []) if entry != path]
        recent.insert(0, path)
        self.config["recent"] = recent[:12]
        save_config(self.config)

    def _populate_recent_menu(self):
        self.recent_menu.clear()
        recent = [path for path in self.config.get("recent", []) if Path(path).is_file()]
        if not recent:
            action = self.recent_menu.addAction("No recent files")
            action.setEnabled(False)
            return
        for path in recent:
            action = self.recent_menu.addAction(Path(path).name)
            action.setToolTip(path)
            action.triggered.connect(lambda checked=False, selected=path: self._open_recent(selected))

    def _open_recent(self, path):
        if not Path(path).is_file():
            self.config["recent"] = [entry for entry in self.config.get("recent", []) if entry != path]
            save_config(self.config)
            return
        self._play_media_path(path)

    def clear_recent(self):
        self.config["recent"] = []
        save_config(self.config)
        self.recent_menu.clear()

    def set_sleep_timer(self, minutes):
        self.sleep_timer.start(minutes)
        self.playback_status.setText(f"sleep timer: {minutes} min")

    def cancel_sleep_timer(self):
        self.sleep_timer.cancel()
        self.playback_status.setText("sleep timer cancelled")

    def _sleep_timer_expired(self):
        self.sleep_timer.cancel()
        self.stop_playback()
        self.playback_status.setText("sleep timer expired")

    def stop_playback(self):
        self.sleep_timer.cancel()
        self.engine.stop()
        self._end_handled = True
        self._current_media_path = None
        self.title_status.clear()
        self.playback_status.setText("stopped")
        self._update_playback_navigation()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file")
        if path:
            path = str(Path(path).resolve())
            if path not in self.config["imported"]:
                self.config["imported"].append(path)
                save_config(self.config)
            self._populate_local_tree()
            self._end_handled = False
            self._seen_playback = False
            self.engine.load(path)
            self._current_media_path = path
            self._add_recent(path)
            self.title_status.setText(Path(path).name)
            self.playback_status.setText("playing")
            self._update_playback_navigation()

    def toggle_pause(self):
        self.engine.command("cycle", "pause")

    def seek(self, seconds):
        self.engine.command("seek", str(seconds), "relative")

    def set_volume(self, value):
        self.engine.command("set", "volume", str(value))

    def _save_volume(self):
        self.config["volume"] = self.volume_slider.value()
        save_config(self.config)

    def toggle_mute(self):
        muted = not bool(self.config.get("muted", False))
        self.config["muted"] = muted
        self.engine.command("set", "mute", "yes" if muted else "no")
        self.volume_button.setIcon(self._icon("volume_off" if muted else "volume"))
        self.volume_button.setToolTip("Unmute" if muted else "Mute")
        save_config(self.config)

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def toggle_left_panel(self):
        visible = not self.left_panel.isVisible()
        self.left_panel.setVisible(visible)
        self.left_toggle_action.setText("Hide list" if visible else "Show list")

    def toggle_right_panel(self):
        visible = not self.right_panel.isVisible()
        self.right_panel.setVisible(visible)
        self.right_toggle_action.setText("Hide sidebar" if visible else "Show sidebar")

    def _update_clock(self):
        self.clock_status.setText(QDateTime.currentDateTime().toString("ddd dd MMM  HH:mm"))

    def closeEvent(self, event):
        self._closing = True
        for thread in self._scan_threads + self._metadata_threads:
            thread.requestInterruption()
        running = [thread for thread in self._scan_threads + self._metadata_threads if thread.isRunning()]
        for thread in running:
            thread.wait(1000)
        running = [thread for thread in self._scan_threads + self._metadata_threads if thread.isRunning()]
        if running:
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
        self.sleep_timer.cancel()
        self.video.close_render_context()
        self.engine.close()
        event.accept()
        super().closeEvent(event)
