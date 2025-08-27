import sys
import os
from random import choice, random, randint
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QDialog,
                               QPushButton, QHBoxLayout, QRadioButton, QButtonGroup, QMenu,
                               QSystemTrayIcon)
# QCursor is now imported from QtGui
from PySide6.QtGui import QPixmap, QMovie, QAction, QIcon, QCursor
# QCursor has been removed from here
from PySide6.QtCore import Qt, QTimer

# Onboarding Speech Bubbles
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

# Feeling Survey Window
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
            'shock_left': QPixmap(os.path.join('images', 'fox', 'fox-shock-left.png')),
            'shock_right': QPixmap(os.path.join('images', 'fox', 'fox-shock-right.png')),
            'post_trauma_left': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-1.png')),
                                 QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-left-2.png'))],
            'post_trauma_right': [QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-1.png')),
                                  QPixmap(os.path.join('images', 'fox', 'fox-post-trauma-right-2.png'))],
            'sleep': QMovie(os.path.join('images', 'fox', 'fox-sleeping.gif')),
        }

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
        initial_x = self.available_geometry.width() - self.width() - 80
        self.move(initial_x, 0)
        self.update_position()

        ### Timers ###
        self.display_check_timer = QTimer(self)
        self.display_check_timer.timeout.connect(self.check_display_changes)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation_frame)
        
        self.state_change_timer = QTimer(self)
        self.state_change_timer.setSingleShot(True)
        self.state_change_timer.timeout.connect(self.switch_state)

        self.walk_logic_timer = QTimer(self)
        self.walk_logic_timer.timeout.connect(self.update_walk_logic)

        self.post_trauma_timer = QTimer(self)
        self.post_trauma_timer.setSingleShot(True)
        self.post_trauma_timer.timeout.connect(self.resume_from_trauma)

        ### State Machine Variables ###
        self.state = 'intro'
        self.frame_index = 0
        self.speed = 2
        self.direction = choice([-1, 1])
        self.turn_new_direction = 1
        self.walk_direction_duration = 0
        self.wonder_count = 0

        ### Mouse Interaction Variables ###
        self.is_dragging = False
        self.drag_start_pos = None

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
        self.animation_timer.start(300)
        QTimer.singleShot(1200, self.ask_question)

    def ask_question(self):
        question = choice(self.questions)
        self.show_bubble(question, word_wrap=False)
        QTimer.singleShot(2000, lambda: self.show_rating_dialog(question))

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
        QTimer.singleShot(3000, self.start_main_lifecycle)

    def show_bubble(self, text, word_wrap=True):
        if self.bubble: self.bubble.deleteLater()
        self.bubble = SpeechBubble(text, self, word_wrap=word_wrap)
        self.bubble.show_smartly_positioned()

    def start_main_lifecycle(self):
        if self.bubble: self.bubble.hide()
        self.display_check_timer.start(2000)
        self.enter_walking_state()

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
        walk_duration_seconds = randint(30, 40)
        self.state_change_timer.start(walk_duration_seconds * 1000)
        self.walk_direction_duration = 0
        self.walk_logic_timer.start(1000)

    def enter_sleeping_state(self):
        self.state = 'sleeping'
        self.animation_timer.stop()
        self.pet_label.setMovie(self.assets['sleep'])
        self.assets['sleep'].start()
        sleep_duration_seconds = randint(10, 20)
        self.state_change_timer.start(sleep_duration_seconds * 1000)

    def update_walk_logic(self):
        if self.state != 'walking': return
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
        if self.state != 'walking': return
        self.state = 'pausing'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)

        QTimer.singleShot(randint(1500, 3000), self.resume_walking)
    
    def initiate_turn(self, new_direction=None):
        if self.state != 'walking': return
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
        if self.state != 'walking': return
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
        if self.state != 'walking': return
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
        if self.state == 'intro': return
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
        if self.state == 'intro': return
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
        if self.is_dragging: return

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
        
        elif self.state == 'intro' or self.state == 'wagging':
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
            # FIX: Changed x() to self.x()
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
