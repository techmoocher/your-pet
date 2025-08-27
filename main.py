import sys
import os
import json
from pathlib import Path
from random import choice, random, randint
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QDialog,
                               QPushButton, QHBoxLayout, QRadioButton, QButtonGroup, QMenu,
                               QSystemTrayIcon, QListWidget, QSlider, QStyle, QListWidgetItem,
                               QGraphicsDropShadowEffect, QFrame)
from PySide6.QtGui import QPixmap, QMovie, QAction, QIcon, QCursor, QColor
from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QPoint
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

### --- MUSIC PLAYER --- ###
class MusicPlayerWindow(QWidget):
    def __init__(self, media_player, tray_actions, parent=None):
        super().__init__(parent)
        self.media_player = media_player
        self.tray_actions = tray_actions
        self.playlist = []
        self.current_index = -1
        self.playback_mode = 'loop_all'
        self.is_muted = False
        self.volume = 1.0
        self.drag_pos = QPoint()

        ### Icons ###
        self.icons = {
            'loop_all': QIcon(os.path.join('images', 'control-buttons', 'loop-all.png')),
            'loop_one': QIcon(os.path.join('images', 'control-buttons', 'loop-1.png')),
            'shuffle': QIcon(os.path.join('images', 'control-buttons', 'shuffle.png')),
            'volume_full': QIcon(os.path.join('images', 'control-buttons', 'volume-full.png')),
            'volume_half': QIcon(os.path.join('images', 'control-buttons', 'volume-half.png')),
            'volume_muted': QIcon(os.path.join('images', 'control-buttons', 'volume-muted.png')),
            'play': QIcon(os.path.join('images', 'control-buttons', 'play.png')),
            'pause': QIcon(os.path.join('images', 'control-buttons', 'pause.png'))
        }

        ### Window Flags and Attributes ###
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Fox Music")
        self.setWindowIcon(QIcon(os.path.join('images', 'logo.png')))
        self.setMinimumSize(420, 220)

        self._setup_ui()
        self._apply_stylesheet()
        self._connect_signals()
        self.scan_music_directory()
        self.load_config()
        self.update_volume_icon()

    ### UI Setup ###
    def _setup_ui(self):
        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("CentralFrame")
        self.main_layout = QVBoxLayout(self.central_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 15)
        self.main_layout.setSpacing(10)
        
        self.setCentralWidget(self.central_frame)

        self._setup_title_bar()

        # Content Layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 10)
        content_layout.setSpacing(15)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(100, 100)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setObjectName("Thumbnail")
        
        title_artist_layout = QVBoxLayout()
        title_artist_layout.setContentsMargins(0, 5, 0, 5)
        self.title_label = QLabel("Welcome to Your Pet Music Player")
        self.title_label.setObjectName("TitleLabel")
        self.artist_label = QLabel("Select a song to start")
        self.artist_label.setObjectName("ArtistLabel")
        title_artist_layout.addWidget(self.title_label)
        title_artist_layout.addWidget(self.artist_label)
        title_artist_layout.addStretch()

        info_layout.addWidget(self.thumbnail_label)
        info_layout.addLayout(title_artist_layout)

        ### Time and Progress ###
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setToolTip("Seek")
        self.total_time_label = QLabel("0:00")
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)

        ### Control Buttons ###
        # Previous Button
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton()
        self.prev_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.prev_button.setFixedSize(48, 48); self.prev_button.setIconSize(QSize(28, 28)); self.prev_button.setObjectName("ControlButton")
        self.prev_button.setToolTip("Previous")

        # Play/Pause Button
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.icons['play'])
        self.play_pause_button.setFixedSize(64, 64); self.play_pause_button.setIconSize(QSize(40, 40)); self.play_pause_button.setObjectName("PlayPauseButton")
        self.play_pause_button.setToolTip("Play")
        # Glow Effect for Play/Pause Button
        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(20)
        shadow_effect.setColor(QColor("#98c379"))
        shadow_effect.setOffset(0, 0)
        self.play_pause_button.setGraphicsEffect(shadow_effect)

        # Next Button
        self.next_button = QPushButton()
        self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.next_button.setFixedSize(48, 48); self.next_button.setIconSize(QSize(28, 28)); self.next_button.setObjectName("ControlButton")
        self.next_button.setToolTip("Next")

        # Control Buttons Layout
        controls_layout.addStretch()
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addStretch()

        # Loop mode options
        options_layout = QHBoxLayout()
        self.loop_button = QPushButton()
        self.loop_button.setIcon(self.icons['loop_all'])
        self.loop_button.setFixedSize(40, 40); self.loop_button.setIconSize(QSize(24, 24)); self.loop_button.setObjectName("ControlButton")
        self.loop_button.setToolTip("Loop All")

        # Playlist Button
        self.songs_list_button = QPushButton("Playlist")
        self.songs_list_button.setObjectName("PlaylistButton")
        self.songs_list_button.setToolTip("Show / Hide Playlist")

        # Volume Button
        volume_layout = QHBoxLayout()
        self.volume_button = QPushButton()
        self.volume_button.setFixedSize(40, 40); self.volume_button.setIconSize(QSize(24, 24)); self.volume_button.setObjectName("ControlButton")
        self.volume_button.setToolTip("Mute / Unmute")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setRange(0, 100); self.volume_slider.setValue(100)
        self.volume_slider.setToolTip("Volume")
        volume_layout.addWidget(self.volume_button)
        volume_layout.addWidget(self.volume_slider)

        options_layout.addWidget(self.loop_button)
        options_layout.addStretch()
        options_layout.addLayout(volume_layout)
        options_layout.addStretch()
        options_layout.addWidget(self.songs_list_button)

        # Playlist Widget
        self.song_list_widget = QListWidget()
        self.song_list_widget.setVisible(False)

        content_layout.addLayout(info_layout)
        content_layout.addLayout(progress_layout)
        content_layout.addLayout(controls_layout)
        content_layout.addLayout(options_layout)
        
        self.main_layout.addLayout(content_layout)
        self.main_layout.addWidget(self.song_list_widget)

    def setCentralWidget(self, widget):
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)

    def _setup_title_bar(self):
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        title_bar_layout.setSpacing(10)

        title_label = QLabel("Fox Music")
        title_label.setStyleSheet("font-weight: bold; color: #9ab;")
        
        self.minimize_button = QPushButton("—")
        self.close_button = QPushButton("✕")
        self.minimize_button.setFixedSize(30, 30)
        self.close_button.setFixedSize(30, 30)
        self.minimize_button.setObjectName("WindowButton")
        self.close_button.setObjectName("WindowButton")

        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.close_button)

        self.main_layout.addWidget(title_bar)
    
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #CentralFrame {
                background-color: #282c34;
                color: #abb2bf;
                font-family: Arial, sans-serif;
                border-radius: 15px;
            }
            #TitleBar {
                background-color: #21252b;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
            #WindowButton {
                font-size: 14px;
                font-weight: bold;
            }
            #WindowButton:hover {
                background-color: #353b45;
            }
            #TitleLabel {
                font-size: 22px; font-weight: bold; color: #ffffff;
            }
            #ArtistLabel {
                font-size: 16px; color: #9ab;
            }
            #Thumbnail {
                border: 1px solid #353b45; border-radius: 10px; background-color: #21252b;
            }
            
            #ControlButton, #PlaylistButton {
                background-color: transparent; border: none;
            }
            #ControlButton:hover, #PlaylistButton:hover {
                background-color: #353b45;
            }
            #ControlButton:pressed, #PlaylistButton:pressed {
                background-color: #21252b;
            }
            #PlayPauseButton {
                border-radius: 32px; background-color: #353b45;
            }
            #PlayPauseButton:hover {
                background-color: #414855;
            }
            #PlayPauseButton:pressed {
                background-color: #21252b;
            }
            #PlaylistButton {
                font-size: 14px; padding: 5px 15px; border: 1px solid #353b45; border-radius: 15px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #282c34; height: 6px; background: #353b45; margin: 2px 0; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #61afef; border: 1px solid #61afef; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px;
            }
            QListWidget {
                background-color: #21252b; border: 1px solid #353b45; font-size: 14px; padding: 5px;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #61afef; color: #282c34; }
            QToolTip { background-color: #21252b; color: #abb2bf; border: 1px solid #353b45; padding: 4px; border-radius: 3px; }
        """)

    def _connect_signals(self):
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.hide)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.next_button.clicked.connect(self.next_song)
        self.prev_button.clicked.connect(self.prev_song)
        self.loop_button.clicked.connect(self.change_playback_mode)
        self.songs_list_button.clicked.connect(self.toggle_song_list)
        self.song_list_widget.itemDoubleClicked.connect(self.play_from_list)
        self.media_player.playbackStateChanged.connect(self.update_play_pause_icon)
        self.media_player.positionChanged.connect(self.update_slider_position)
        self.media_player.durationChanged.connect(self.set_slider_range)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.progress_slider.sliderMoved.connect(self.media_player.setPosition)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_button.clicked.connect(self.toggle_mute)
        
    def _format_time(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    ### Music Directory Scanner ###
    def scan_music_directory(self):
        music_dir = Path("./music")
        self.playlist = []
        self.song_list_widget.clear()
        if not music_dir.exists():
            return

        for song_dir in music_dir.iterdir():
            if song_dir.is_dir():
                mp3_files = list(song_dir.glob('*.mp3'))
                if not mp3_files:
                    continue
                
                mp3_path = mp3_files[0]
                title, artist = "Unknown Title", "Unknown Artist"
                filename_stem = mp3_path.stem
                if '_' in filename_stem:
                    parts = filename_stem.split('_', 1)
                    title = parts[0].replace('-', ' ')
                    if len(parts) > 1:
                        artist = parts[1].replace('-', ' ')
                else:
                    title = filename_stem.replace('-', ' ')

                thumbnail_path = None
                for ext in ['.jpg', '.png', '.jfif']:
                    if (song_dir / f"thumbnail{ext}").exists():
                        thumbnail_path = song_dir / f"thumbnail{ext}"
                        break

                song_data = {"title": title, "artist": artist, "path": mp3_path, "thumbnail": thumbnail_path}
                self.playlist.append(song_data)
                item = QListWidgetItem(f"{song_data['title']} - {song_data['artist']}")
                self.song_list_widget.addItem(item)
        
        if not self.playlist:
            self.title_label.setText("No music found")
            self.artist_label.setText("Check ./music folder structure")

    def set_initial_position(self, position):
        self.media_player.setPosition(position)
        try:
            self.media_player.durationChanged.disconnect()
        except RuntimeError:
            pass 
        self.media_player.durationChanged.connect(self.set_slider_range)

    def play_song(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            song = self.playlist[index]
            self.media_player.setSource(QUrl.fromLocalFile(str(song['path'].absolute())))
            self.media_player.play()
            self.title_label.setText(song['title'])
            self.artist_label.setText(song['artist'])
            if song['thumbnail']:
                self.thumbnail_label.setPixmap(QPixmap(str(song['thumbnail'])).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.thumbnail_label.setPixmap(QPixmap())
                self.thumbnail_label.setText("No Art")
            self.song_list_widget.setCurrentRow(index)

    def next_song(self):
        if not self.playlist: return
        if self.playback_mode == 'loop_one': self.play_song(self.current_index)
        elif self.playback_mode == 'shuffle': self.play_song(randint(0, len(self.playlist) - 1))
        else: self.play_song((self.current_index + 1) % len(self.playlist))

    def prev_song(self):
        if not self.playlist: return
        self.play_song((self.current_index - 1 + len(self.playlist)) % len(self.playlist))

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.current_index == -1 and self.playlist:
                self.play_song(0)
            else:
                self.media_player.play()

    def change_playback_mode(self):
        if self.playback_mode == 'loop_all': 
            self.playback_mode = 'loop_one'
            self.loop_button.setIcon(self.icons['loop_one'])
            self.loop_button.setToolTip("Loop One")
            self.tray_actions['loop'].setText("Mode: Loop One")
        elif self.playback_mode == 'loop_one': 
            self.playback_mode = 'shuffle'
            self.loop_button.setIcon(self.icons['shuffle'])
            self.loop_button.setToolTip("Shuffle")
            self.tray_actions['loop'].setText("Mode: Shuffle")
        else: 
            self.playback_mode = 'loop_all'
            self.loop_button.setIcon(self.icons['loop_all'])
            self.loop_button.setToolTip("Loop All")
            self.tray_actions['loop'].setText("Mode: Loop All")

    def set_volume(self, value):
        self.volume = value / 100.0
        self.media_player.audioOutput().setVolume(self.volume)
        if self.is_muted and value > 0:
            self.is_muted = False
        self.update_volume_icon()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.media_player.audioOutput().setMuted(self.is_muted)
        self.update_volume_icon()
        self.tray_actions['mute'].setText("Unmute" if self.is_muted else "Mute")

    def update_volume_icon(self):
        if self.is_muted or self.volume == 0:
            self.volume_button.setIcon(self.icons['volume_muted'])
        elif self.volume < 0.5:
            self.volume_button.setIcon(self.icons['volume_half'])
        else:
            self.volume_button.setIcon(self.icons['volume_full'])

    def toggle_song_list(self):
        self.song_list_widget.setVisible(not self.song_list_widget.isVisible())
        self.adjustSize()

    def play_from_list(self, item):
        self.play_song(self.song_list_widget.row(item))

    def update_play_pause_icon(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(self.icons['pause'])
            self.play_pause_button.setToolTip("Pause")
            self.tray_actions['play_pause'].setText("Pause")
        else:
            self.play_pause_button.setIcon(self.icons['play'])
            self.play_pause_button.setToolTip("Play")
            self.tray_actions['play_pause'].setText("Play")

    def update_slider_position(self, position):
        self.progress_slider.setValue(position)
        self.current_time_label.setText(self._format_time(position))

    def set_slider_range(self, duration):
        self.progress_slider.setRange(0, duration)
        self.total_time_label.setText(self._format_time(duration))

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_song()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

### --- Onboarding Speech Bubbles --- ###
class SpeechBubble(QWidget):
    def __init__(self, text, parent, word_wrap=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet("background-color: white; color: black; border: 1px solid black; border-radius: 10px; padding: 10px;")
        if word_wrap:
            self.label.setWordWrap(True)
            self.label.setMaximumWidth(270)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def show_smartly_positioned(self):
        parent_geometry = self.parent().geometry()
        x = parent_geometry.center().x() - self.width() / 2
        y_above = parent_geometry.top() - self.height() - 5
        self.move(int(x), int(y_above if y_above > 0 else parent_geometry.bottom() + 5))
        self.show()

### --- Feeling Survey Window --- ###
class RatingDialog(QDialog):
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How are you feeling?")
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(question))
        emoticons = {1: "😭", 2: "😞", 3: "😑", 4: "😊", 5: "😁"}
        self.button_group = QButtonGroup(self)
        radio_layout = QHBoxLayout()
        for i in range(1, 6):
            radio_button = QRadioButton(emoticons[i])
            radio_layout.addWidget(radio_button)
            self.button_group.addButton(radio_button, i)
        self.button_group.button(3).setChecked(True)
        self.layout.addLayout(radio_layout)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        self.layout.addWidget(self.confirm_button)
        self.setLayout(self.layout)

    def get_rating(self):
        return self.button_group.checkedId()

### --- Desktop Pet --- ###
class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        ### Animations Assets ###
        self.assets = {
            'idle': [QPixmap(os.path.join('images', 'fox', 'fox-1.png')), QPixmap(os.path.join('images', 'fox', 'fox-2.png'))],
            'walk_left': [QPixmap(os.path.join('images', 'fox', 'fox-walking-left-1.png')), QPixmap(os.path.join('images', 'fox', 'fox-walking-left-2.png'))],
            'walk_right': [QPixmap(os.path.join('images', 'fox', 'fox-walking-right-1.png')), QPixmap(os.path.join('images', 'fox', 'fox-walking-right-2.png'))],
            'posture_idle_left': QPixmap(os.path.join('images', 'fox', 'fox-idle-left.png')),
            'posture_idle_right': QPixmap(os.path.join('images', 'fox', 'fox-idle-right.png')),
            'shock_left': QPixmap(os.path.join('images', 'fox', 'fox-shock-left.png')),
            'shock_right': QPixmap(os.path.join('images', 'fox', 'fox-shock-right.png')),
            'post_trauma_left': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-1.png')), QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-2.png'))],
            'post_trauma_right': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-1.png')), QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-2.png'))],
            'sleep': QMovie(os.path.join('images', 'fox', 'fox-sleeping.gif')),
        }

        ### Onboarding Questions and Responses ###
        self.questions = ["How's your day going?",
                          "How are you doing?",
                          "How's your day been?"]
        self.responses = {
            1: ["I know it's hard right now, but keep going!", "A bad day doesn't mean a bad life. You've got this!", "I'm always here for you!", "Take a deep breath, you got this!"],
            2: ["Don't worry, you have me by your side.", "Let's find something to make you smile!", "It may be hard but you've got this!"],
            3: ["Let's make the rest of the day a great one!", "Keep it up, you're doing well!", "Not bad, let's see how we can make it better!"],
            4: ["That's great to hear! Let's keep it up.", "Awesome! You're doing great.",  "Let's celebrate your day!"],
            5: ["Wow, how amazing! I'm happy for you.", "That's fantastic!", "Let's celebrate!", "I'm so glad to hear that! Keep shining!"]
        }
        self.bubble = None

        ### Layout ###
        self.layout = QVBoxLayout()
        self.pet_label = QLabel(self)
        self.pet_label.setPixmap(self.assets['idle'][0])
        self.layout.addWidget(self.pet_label)
        self.setLayout(self.layout)
        self.resize(self.assets['idle'][0].size())

        ### Screen Geometry & Initial Position ###
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        initial_x = self.available_geometry.width() - self.width() - 80
        self.move(initial_x, 0)
        self.update_position()

        ### Timers ###
        # Display Check Timer
        self.display_check_timer = QTimer(self)
        self.display_check_timer.timeout.connect(self.check_display_changes)

        # Animation Timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation_frame)

        # State Change Timer
        self.state_change_timer = QTimer(self)
        self.state_change_timer.setSingleShot(True)
        self.state_change_timer.timeout.connect(self.switch_state)

        # Walk Logic Timer
        self.walk_logic_timer = QTimer(self)
        self.walk_logic_timer.timeout.connect(self.update_walk_logic)

        # Post Trauma Timer
        self.post_trauma_timer = QTimer(self)
        self.post_trauma_timer.setSingleShot(True)
        self.post_trauma_timer.timeout.connect(self.resume_from_trauma)

        ### State Initialization ###
        self.state = 'intro'
        self.frame_index = 0
        self.speed = 2
        self.direction = choice([-1, 1])
        self.turn_new_direction = 1
        self.walk_direction_duration = 0
        self.wonder_count = 0
        self.is_dragging = False
        self.drag_start_pos = None

        ### Music Player Initialization ###
        self._initialize_music_player()
        self.setup_tray_icon()
        self.start_intro_sequence()
        self.show()
        
        app = QApplication.instance()
        app.aboutToQuit.connect(self.save_config)

    def _initialize_music_player(self):
        self.tray_actions = {
            'play_pause': QAction("Play"),
            'prev': QAction("Previous"),
            'next': QAction("Next"),
            'loop': QAction("Mode: Loop All"),
            'mute': QAction("Mute"),
            'open': QAction("Open Player")
        }
        self.media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self._audio_output)
        self.music_player_window = MusicPlayerWindow(self.media_player, self.tray_actions)

    def save_config(self):
        if not self.music_player_window or not self.media_player:
            return
        
        config_data = {
            "last_track_index": self.music_player_window.current_index,
            "last_position": self.media_player.position(),
            "volume": self.music_player_window.volume_slider.value(),
            "is_muted": self.media_player.audioOutput().isMuted(),
            "playback_mode": self.music_player_window.playback_mode
        }
        
        try:
            with open("config.json", 'w') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join('images', 'logo.png')))
        self.tray_icon.setToolTip("Your Pet")
        
        tray_menu = QMenu()
        
        self.music_menu = QMenu("Music")
        
        self.tray_actions['play_pause'].triggered.connect(self.music_player_window.toggle_play_pause)
        self.tray_actions['prev'].triggered.connect(self.music_player_window.prev_song)
        self.tray_actions['next'].triggered.connect(self.music_player_window.next_song)
        self.tray_actions['loop'].triggered.connect(self.music_player_window.change_playback_mode)
        self.tray_actions['mute'].triggered.connect(self.music_player_window.toggle_mute)
        self.tray_actions['open'].triggered.connect(self.open_music_player)

        self.music_menu.addAction(self.tray_actions['play_pause'])
        self.music_menu.addAction(self.tray_actions['prev'])
        self.music_menu.addAction(self.tray_actions['next'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(self.tray_actions['loop'])
        self.music_menu.addAction(self.tray_actions['mute'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(self.tray_actions['open'])
        
        tray_menu.addMenu(self.music_menu)

        self.toggle_action = QAction("Hide", self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)
        tray_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def open_music_player(self):
        self.music_player_window.show()
        self.music_player_window.activateWindow()

    def start_intro_sequence(self):
        self.music_menu.setEnabled(False)
        hour = datetime.now().hour
        greeting = "Good morning!" if 5 <= hour < 12 else "Good afternoon!" if 12 <= hour < 18 else "Good evening!"
        self.show_bubble(greeting)
        self.animation_timer.start(300)
        QTimer.singleShot(1200, self.ask_question)

    def start_main_lifecycle(self):
        self.music_menu.setEnabled(True)
        if self.bubble:
            self.bubble.hide()
        self.display_check_timer.start(2000)
        self.enter_walking_state()
    
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("Show")
        else:
            self.show()
            self.toggle_action.setText("Hide")

    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()

    def ask_question(self):
        question = choice(self.questions)
        self.show_bubble(question, word_wrap=False)
        QTimer.singleShot(2000, lambda: self.show_rating_dialog(question))

    def show_rating_dialog(self, question_text):
        if self.bubble:
            self.bubble.hide()
        dialog = RatingDialog(question_text, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.show_response(dialog.get_rating())
        else:
            self.start_main_lifecycle()

    def show_response(self, rating):
        response_text = choice(self.responses[rating])
        self.show_bubble(response_text)
        QTimer.singleShot(3000, self.start_main_lifecycle)

    def show_bubble(self, text, word_wrap=True):
        if self.bubble:
            self.bubble.deleteLater()
        self.bubble = SpeechBubble(text, self, word_wrap=word_wrap)
        self.bubble.show_smartly_positioned()

    def switch_state(self):
        if self.state == 'walking':
            self.state = 'idling_before_sleep'
            self.walk_logic_timer.stop()
            self.animation_timer.stop()
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            QTimer.singleShot(randint(700, 1200), self.enter_sleeping_state)
        elif self.state == 'sleeping':
            self.state = 'waking_up'
            self.assets['sleep'].stop()
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            QTimer.singleShot(randint(700, 1200), self.enter_walking_state)

    def enter_walking_state(self):
        self.state = 'walking'
        self.animation_timer.setInterval(150)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self.state_change_timer.start(randint(30, 40) * 1000)
        self.walk_direction_duration = 0
        self.walk_logic_timer.start(1000)

    def enter_sleeping_state(self):
        self.state = 'sleeping'
        self.animation_timer.stop()
        self.pet_label.setMovie(self.assets['sleep'])
        self.assets['sleep'].start()
        self.state_change_timer.start(randint(10, 20) * 1000)

    def update_walk_logic(self):
        if self.state != 'walking':
            return
        self.walk_direction_duration += 1
        r = random()
        if r < 0.04:
            self.initiate_wagging()
        elif r < 0.09:
            self.initiate_pause()
        elif r < 0.14:
            self.initiate_wondering()
        elif r < 0.22:
            self.initiate_turn()
        elif self.walk_direction_duration > 15:
            self.initiate_turn()

    def initiate_pause(self):
        if self.state != 'walking':
            return
        self.state = 'pausing'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(1500, 3000), self.resume_walking)

    def initiate_turn(self, new_direction=None):
        if self.state != 'walking':
            return
        self.state = 'turning'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        self.turn_new_direction = new_direction if new_direction is not None else self.direction * -1
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(300, 500), self.complete_turn)

    def complete_turn(self):
        self.direction = self.turn_new_direction
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(300, 500), self.resume_walking)

    def initiate_wondering(self):
        if self.state != 'walking':
            return
        self.state = 'wondering'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        self.wonder_count = randint(1, 3)
        self.perform_wonder_step()

    def perform_wonder_step(self):
        self.wonder_count -= 1
        self.direction *= -1
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        if self.wonder_count > 0:
            QTimer.singleShot(randint(600, 1000), self.perform_wonder_step)
        else:
            QTimer.singleShot(randint(500, 800), self.resume_walking)

    def initiate_wagging(self):
        if self.state != 'walking':
            return
        self.state = 'wagging'
        self.walk_logic_timer.stop()
        self.animation_timer.setInterval(300)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        QTimer.singleShot(randint(1500, 3000), self.resume_walking)

    def resume_walking(self):
        self.state = 'walking'
        self.animation_timer.setInterval(150)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self.walk_direction_duration = 0
        self.walk_logic_timer.start(1000)

    def mousePressEvent(self, event):
        if self.state == 'intro':
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition()
            self.state_change_timer.stop()
            self.walk_logic_timer.stop()
            self.animation_timer.stop()
            self.assets['sleep'].stop()
            self.state = 'shock'
            shock_sprite = self.assets['shock_right'] if self.direction == 1 else self.assets['shock_left']
            self.pet_label.setPixmap(shock_sprite)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.globalPosition() - self.drag_start_pos
            self.move(self.pos() + delta.toPoint())
            self.drag_start_pos = event.globalPosition()

    def mouseReleaseEvent(self, event):
        if self.state == 'intro':
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start_pos = None
            self.move(self.x(), self.base_y)
            self.state = 'post_trauma'
            self.frame_index = 0
            self.animation_timer.setInterval(300)
            if not self.animation_timer.isActive():
                self.animation_timer.start()
            self.post_trauma_timer.start(randint(2000, 3000))

    def resume_from_trauma(self):
        self.state = 'recovering'
        self.animation_timer.stop()
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(500, 1000), self.start_main_lifecycle)

    def update_animation_frame(self):
        if self.is_dragging:
            return
        if self.state == 'walking':
            if (self.x() >= self.available_geometry.width() - self.width() and self.direction == 1):
                self.initiate_turn(new_direction=-1)
                return
            elif (self.x() <= 0 and self.direction == -1):
                self.initiate_turn(new_direction=1)
                return
            self.move(self.x() + (self.speed * self.direction), self.y())
            frames = self.assets['walk_right'] if self.direction == 1 else self.assets['walk_left']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])
        elif self.state == 'post_trauma':
            frames = self.assets['post_trauma_right'] if self.direction == 1 else self.assets['post_trauma_left']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])
        elif self.state in ['intro', 'wagging']:
            frames = self.assets['idle']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])

    def update_position(self):
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        self.base_y = self.available_geometry.height() - self.height() - 10
        if not (0 <= self.x() <= self.available_geometry.width() - self.width()):
            x = self.available_geometry.width() - self.width() - 50
            self.move(x, self.base_y)
        else:
            self.move(self.x(), self.base_y)

    def check_display_changes(self):
        current_screen = QApplication.primaryScreen().geometry()
        current_available = QApplication.primaryScreen().availableGeometry()
        if (current_screen != self.screen_geometry or current_available != self.available_geometry):
            self.screen_geometry = current_screen
            self.available_geometry = current_available
            self.update_position()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())
