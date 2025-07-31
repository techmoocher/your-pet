import sys
import os
from random import choice, random, randint
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QDialog, QPushButton,
                               QHBoxLayout, QRadioButton, QButtonGroup, QMenu, QSystemTrayIcon,
                               QLineEdit, QTextEdit, QStyle)
from PySide6.QtGui import QPixmap, QMovie, QCursor, QAction, QIcon
from PySide6.QtCore import Qt, QTimer, QPoint, Signal

class ChatWindow(QDialog):
    message_sent = Signal(str)
    window_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chat with Fox")
        self.setMinimumSize(400, 500)

        # Main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Conversation history view
        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.layout.addWidget(self.history_view)

        # Input layout
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Say something...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.send_button.setIcon(icon)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

    def send_message(self):
        text = self.input_field.text().strip()
        if text:
            self.add_message(text, is_user=True)
            self.message_sent.emit(text)
            self.input_field.clear()

    def add_message(self, text, is_user):
        if is_user:
            align = "right"
            name = "You"
            bg_color = "#00c4ff"
        else:
            align = "left"
            name = "Fox"
            bg_color = "#ecac0d"

        message_html = f"""
        <div align="{align}">
            <div style="background-color: {bg_color}; display: inline-block; padding: 8px; border-radius: 8px; max-width: 80%;">
                <b>{name}</b><br>
                {text.replace('\n', '<br>')}
            </div>
        </div>
        """
        self.history_view.append(message_html)
        self.history_view.verticalScrollBar().setValue(self.history_view.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        self.window_closed.emit()


class SpeechBubble(QWidget):
    def __init__(self, text, parent, word_wrap=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            background-color: white; 
            color: black; 
            border: 1px solid black; 
            border-radius: 10px; 
            padding: 10px;
        """)

        if word_wrap:
            self.label.setWordWrap(True)
            self.label.setMaximumWidth(270)
        
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
    
    def show_smartly_positioned(self):
        parent_geometry = self.parent().geometry()
        screen_available_geometry = QApplication.primaryScreen().availableGeometry()
        x = parent_geometry.center().x() - self.width() / 2

        y_above = parent_geometry.top() - self.height() - 5 
        
        if y_above < screen_available_geometry.top():
            y = parent_geometry.bottom() + 5
        else:
            y = y_above
        self.move(int(x), int(y))
        self.show()

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


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()

        ### Window Settings ###
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        ### Assets ###
        self.assets = {
            'idle': [QPixmap(os.path.join('images', 'fox', 'fox-1.png')),
                     QPixmap(os.path.join('images', 'fox', 'fox-2.png'))],
            'walk_left': [QPixmap(os.path.join('images', 'fox', 'fox-walking-left-1.png')),
                          QPixmap(os.path.join('images', 'fox', 'fox-walking-left-2.png'))],
            'walk_right': [QPixmap(os.path.join('images', 'fox', 'fox-walking-right-1.png')),
                           QPixmap(os.path.join('images', 'fox', 'fox-walking-right-2.png'))],
            'posture_idle_left': QPixmap(os.path.join('images', 'fox', 'fox-idle-left.png')),
            'posture_idle_right': QPixmap(os.path.join('images', 'fox', 'fox-idle-right.png')),
            'comfy': QPixmap(os.path.join('images', 'fox', 'fox-comfy.png')),
            'sleep': QMovie(os.path.join('images', 'fox', 'fox-sleeping.gif')),
            'shock_left': QPixmap(os.path.join('images', 'fox', 'fox-shock-left.png')),
            'shock_right': QPixmap(os.path.join('images', 'fox', 'fox-shock-right.png')),
            'post_trauma_left': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-1.png')),
                                 QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-2.png'))],
            'post_trauma_right': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-1.png')),
                                  QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-2.png'))]
        }

        self.questions = ["How's your day going?",
                          "How are you doing?",
                          "How's your day been going?"]
        self.responses = {
            1: ["I know it's hard right now, but keep going!", "A bad day doesn't mean a bad life. You've got this!", "Remember that I'm here for you!", "Take a deep breath, things might not be as bad as you think."],
            2: ["There may be some hard days, but don't worry, you have me by your side.", "Hope you can enjoy the rest of your day.", "Let's find something to make you smile!", "It may be hard but you've got this! Just keep going!"],
            3: ["An average day is a good foundation to build on!", "Let's make the rest of the day a great one!","Keep it up, you're doing well!", "Not bad, let's see how we can make it better!"],
            4: ["That's great to hear! Let's keep the good vibes going.", "Awesome! You're doing great.", "Love that for you!", "Let's celebrate your day!"],
            5: ["Wow, an amazing day! I'm so happy to hear so.", "That's fantastic!", "Let's celebrate!", "I'm so glad to hear that! Keep shining!"]
        }
        self.bubble = None
        self.chat_window = None

        ### UI Setup ###
        self.layout = QVBoxLayout()
        self.pet_label = QLabel(self)
        self.pet_label.setPixmap(self.assets['idle'][0])
        self.layout.addWidget(self.pet_label)
        self.setLayout(self.layout)
        self.resize(self.assets['idle'][0].size())

        ### Screen Geometry ###
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        self.update_position()

        ### Timers ###
        self.display_check_timer = QTimer(self)
        self.display_check_timer.timeout.connect(self.check_display_changes)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation_frame)
        
        self.state_timer = QTimer(self)
        self.state_timer.setSingleShot(True)
        self.state_timer.timeout.connect(self.decide_next_state)

        self.walk_direction_timer = QTimer(self)
        self.walk_direction_timer.timeout.connect(self.update_walk_direction)

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.enter_inactivity_sleep)

        ### State Machine Variables ###
        self.state = 'intro'
        self.paused_walk_timer_remaining = -1
        self.frame_index = 0
        self.speed = 2
        self.direction = 1
        self.walk_direction_duration = 0
        self.turn_step = 0
        self.turn_new_direction = 1
        self.user_has_interacted = False

        ### Mouse Interaction Variables ###
        self.paused_state_timer_remaining = -1
        self.paused_state = None
        self.mouse_history = []
        self.direction_changes = 0
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_direction = 1

        ### System Tray Icon ###
        self.setup_tray_icon()

        ### Start the Intro Sequence ###
        self.start_intro_sequence()
        self.show()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = os.path.join('images', 'logo.png')
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Your Pet")
        
        tray_menu = QMenu()

        self.toggle_action = QAction("Hide", self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)

        # talk_action = QAction("Talk", self)
        # talk_action.triggered.connect(self.open_chat_window)
        # tray_menu.addAction(talk_action)

        tray_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

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

    def start_intro_sequence(self):
        hour = datetime.now().hour
        if 5 <= hour < 12: greeting = "Good morning!"
        elif 12 <= hour < 18: greeting = "Good afternoon!"
        else: greeting = "Good evening!"
        
        self.show_bubble(greeting)
        QTimer.singleShot(1200, self.ask_question)

    def ask_question(self):
        question = choice(self.questions)
        self.show_bubble(question, word_wrap=False)

        QTimer.singleShot(2100, lambda: self.show_rating_dialog(question))

    def show_rating_dialog(self, question_text):
        if self.bubble: self.bubble.hide()

        dialog = RatingDialog(question_text, self)
        if dialog.exec() == QDialog.Accepted:
            rating = dialog.get_rating()
            self.show_response(rating)
        else:
            self.start_main_lifecycle()

    def show_response(self, rating):
        response_text = choice(self.responses[rating])
        self.show_bubble(response_text)
        QTimer.singleShot(5000, self.start_main_lifecycle)

    def show_bubble(self, text, word_wrap=True):
        if self.bubble: self.bubble.deleteLater()
        self.bubble = SpeechBubble(text, self, word_wrap=word_wrap)
        self.bubble.show_smartly_positioned()
        
    def start_main_lifecycle(self):
        if self.bubble: self.bubble.hide()

        # Start the global timers
        self.display_check_timer.start(2000)
        self.animation_timer.start(150)
        self.inactivity_timer.start(300000)

        self.state = 'post_intro_idle'
        self.pet_label.setPixmap(self.assets['idle'][0])

        QTimer.singleShot(300, self.prepare_first_walk)

    ### State Management Functions ###
    def prepare_first_walk(self):
        self.direction = choice([-1, 1])

        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)

        QTimer.singleShot(200, self.enter_walking_state)

    def enter_inactivity_sleep(self):
        if self.state == 'inactivity_sleep':
            return
            
        self.paused_state_timer_remaining = self.state_timer.remainingTime()
        self.paused_state = self.state
        self.state_timer.stop()
        self.walk_direction_timer.stop()
        
        self.state = 'inactivity_sleep'
        self.pet_label.setMovie(self.assets['sleep'])
        self.assets['sleep'].start()
    
    def enter_walking_state(self):
        self.state = 'walking'
        self.state_timer.start(randint(60, 120) * 1000)
        self.walk_direction_timer.start(1000)
        self.update_walk_direction()

    def start_turning(self, new_direction):
        if self.state == 'turning': return

        self.paused_walk_timer_remaining = self.state_timer.remainingTime()
        self.state_timer.stop()

        self.state = 'turning'
        self.turn_step = 0
        self.turn_new_direction = new_direction
        self.walk_direction_timer.stop()
        self.handle_turn_sequence()

    def handle_turn_sequence(self):
        if self.is_dragging:
            return
        
        if self.turn_step == 0:
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            self.turn_step = 1
            QTimer.singleShot(randint(500, 1500), self.handle_turn_sequence)
        elif self.turn_step == 1:
            self.direction = self.turn_new_direction
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            self.turn_step = 2
            QTimer.singleShot(randint(500, 1000), self.handle_turn_sequence)
        elif self.turn_step == 2:
            self.state = 'walking'
            if self.paused_walk_timer_remaining > 0:
                self.state_timer.start(self.paused_walk_timer_remaining)
            self.walk_direction_timer.start(1000)

    def decide_next_state(self):
        if self.is_dragging:
            return
        
        self.enter_walking_state()

    def start_post_trauma_sequence(self):
        self.state = 'post_trauma'

        self.move(self.x(), self.base_y)

        trauma_sprites = self.assets['post_trauma_right'] if self.drag_direction == 1 else self.assets['post_trauma_left']
        self.pet_label.setPixmap(trauma_sprites[0])

        QTimer.singleShot(150, lambda: self.pet_label.setPixmap(trauma_sprites[1]))
        def show_posture():
            idle_sprite = self.assets['posture_idle_right'] if self.drag_direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            QTimer.singleShot(1000, self.restore_paused_state)
            
        QTimer.singleShot(1150, show_posture)

    def mousePressEvent(self, event):
        if self.state == 'intro':
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.user_has_interacted = True
            self.inactivity_timer.start(300000)

            if self.state in ['walking', 'inactivity_sleep', 'post_intro_idle', 'resuming_idle']:
                self.paused_state = self.state
                self.paused_state_timer_remaining = self.state_timer.remainingTime()
                self.state_timer.stop()
                self.walk_direction_timer.stop()

                if self.state == 'inactivity_sleep':
                    self.assets['sleep'].stop()

            self.drag_start_pos = event.globalPosition()

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None:
            if not self.is_dragging:
                self.is_dragging = True
                self.state = 'dragging'

                if self.paused_state == 'inactivity_sleep':
                    self.drag_direction = -1
                else:
                    self.drag_direction = self.direction
                
                shock_sprite = self.assets['shock_right'] if self.drag_direction == 1 else self.assets['shock_left']
                self.pet_label.setPixmap(shock_sprite)

            delta = event.globalPosition() - self.drag_start_pos
            self.move(self.pos() + delta.toPoint())
            self.drag_start_pos = event.globalPosition()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                self.is_dragging = False
                self.drag_start_pos = None
                self.start_post_trauma_sequence()
            else:
                self.drag_start_pos = None
                if self.paused_state is not None:
                    self.restore_paused_state()

    def check_mouse_hover(self):
        if self.is_dragging:
            return

        mouse_pos = QCursor.pos()
        if self.geometry().contains(mouse_pos):
            self.user_has_interacted = True
            self.inactivity_timer.start(300000)
            self.track_mouse_movement(mouse_pos.x())
        else:
            self.mouse_history.clear()
            self.direction_changes = 0

    def track_mouse_movement(self, current_x):
        if not self.mouse_history: self.mouse_history.append(current_x); return
        last_x = self.mouse_history[-1]
        self.mouse_history.append(current_x)
        if len(self.mouse_history) > 10: self.mouse_history.pop(0)
        current_direction = 1 if current_x > last_x else -1
        last_direction = 1 if last_x > self.mouse_history[-2] else -1 if len(self.mouse_history) > 1 else 0
        if current_direction != last_direction: self.direction_changes += 1

    def restore_paused_state(self):
        if self.paused_state:
            self.state = self.paused_state
        else:
            self.enter_walking_state()
            return

        if self.state == 'walking':
            self.walk_direction_timer.start(1000)
        elif self.state == 'inactivity_sleep':
            self.assets['sleep'].stop()
            self.enter_walking_state()
            return

        if self.paused_state_timer_remaining > 0:
            self.state_timer.start(self.paused_state_timer_remaining)
        else:
            self.decide_next_state()

        self.paused_state_timer_remaining = -1
        self.paused_state = None

    def update_animation_frame(self):
        if self.state in ['intro', 'inactivity_sleep', 'turning', 'dragging', 'post_trauma']:
            return

        self.check_mouse_hover()
        
        if self.state == 'talking':
            self.frame_index = (self.frame_index + 1) % len(self.assets['idle'])
            self.pet_label.setPixmap(self.assets['idle'][self.frame_index])
            return

        if self.direction_changes > 3:
            self.pet_label.setPixmap(self.assets['comfy'])
        else:
            if self.state == 'walking':
                if (self.x() >= self.available_geometry.width() - self.width() and self.direction == 1):
                    self.start_turning(-1)
                    return
                elif (self.x() <= 0 and self.direction == -1):
                    self.start_turning(1)
                    return

                self.move(self.x() + (self.speed * self.direction), self.y())
                frames = self.assets['walk_right'] if self.direction == 1 else self.assets['walk_left']
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.pet_label.setPixmap(frames[self.frame_index])

            elif self.state in ['post_intro_idle', 'resuming_idle']:
                frames = self.assets['idle']
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.pet_label.setPixmap(frames[self.frame_index])

    def update_walk_direction(self):
        if self.is_dragging or self.state != 'walking':
            return
        
        self.walk_direction_duration += 1
        if random() < 0.30 or self.walk_direction_duration > 30:
            self.start_turning(self.direction * -1)
            self.walk_direction_duration = 0

    def update_position(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        x = self.available_geometry.width() - self.width() - int(screen_geometry.width() * 0.01) - 50
        self.base_y = self.available_geometry.height() - self.height() - 10
        self.move(x, self.base_y)
    
    def check_display_changes(self):
        current_screen = QApplication.primaryScreen().geometry()
        current_available = QApplication.primaryScreen().availableGeometry()
        if (current_screen != self.screen_geometry or current_available != self.available_geometry):
            self.screen_geometry = current_screen
            self.available_geometry = current_available
            self.update_position()

    def open_chat_window(self):
        if self.state in ['intro', 'dragging', 'post_trauma']:
            return

        if self.state != 'talking':
            if self.state in ['walking', 'inactivity_sleep', 'post_intro_idle', 'resuming_idle']:
                self.paused_state = self.state
                self.paused_state_timer_remaining = self.state_timer.remainingTime()
                self.state_timer.stop()
                self.walk_direction_timer.stop()
                if self.state == 'inactivity_sleep':
                    self.assets['sleep'].stop()

            self.state = 'talking'
            self.frame_index = 0
            self.pet_label.setPixmap(self.assets['idle'][self.frame_index])

        if self.chat_window is None:
            self.chat_window = ChatWindow()
            self.chat_window.message_sent.connect(self.process_chat_message)
            self.chat_window.window_closed.connect(self.chat_window_was_closed)
        
        self.chat_window.show()
        self.chat_window.activateWindow()

    def chat_window_was_closed(self):
        self.restore_paused_state()

    def process_chat_message(self, text):
        response = "I'm a fox of few words for now, but I love listening!"
        self.chat_window.add_message(response, is_user=False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())