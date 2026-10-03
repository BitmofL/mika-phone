from PyQt6.QtGui import QTransform, QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QComboBox, QLineEdit, QSlider,
    QScrollArea, QDialog, QFormLayout, QDialogButtonBox, QFileDialog
)
from PyQt6.QtGui import QPixmap, QCursor
import sys
import sounddevice as sd
from Mika_main import VoiceAssistant
import locale
import random
locale.setlocale(locale.LC_ALL, 'Russian')
from PyQt6.QtCore import QLocale
QLocale.setDefault(QLocale("ru_RU"))

class FaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 500)
        self.eye_state = "closed"

        self.face_closed = QPixmap("images/Mika_close.png").scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.face_open = QPixmap("images/Mika_open.png").scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)

        self.blink_duration_timer = QTimer(self)
        self.blink_duration_timer.setSingleShot(True)
        self.blink_duration_timer.timeout.connect(self.end_blink)

    def start_animation(self):
        self.eye_state = "open"
        self.start_blink_timer()
        self.update()

    def stop_animation(self):
        self.eye_state = "closed"
        self.blink_timer.stop()
        self.update()

    def start_blink_timer(self):
        interval = random.randint(2000, 4000)
        self.blink_timer.setInterval(interval)
        self.blink_timer.start()

    def blink(self):
        self.eye_state = "blinking"
        self.update()
        self.blink_duration_timer.start(200)
        interval = random.randint(2000, 4000)
        self.blink_timer.setInterval(interval)

    def end_blink(self):
        if self.eye_state == "blinking":
            self.eye_state = "open"
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        current_pixmap = self.face_closed if self.eye_state in ["closed", "blinking"] else self.face_open
        painter.drawPixmap(0, 0, current_pixmap)

class DeviceTile(QWidget):
    def __init__(self, device_name, image_path, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(140, 160)
        self.setStyleSheet("""
            background-color: #2E2E2E;
            border-radius: 15px;
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        self.icon_label = QLabel()
        pixmap = QPixmap(image_path).scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel(device_name)
        self.text_label.setStyleSheet("color: white; font-size: 12px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)

        self.trash_button = QPushButton()
        trash_pixmap = QPixmap("fotos/trash.PNG").scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        from PyQt6.QtGui import QIcon
        self.trash_button.setIcon(QIcon(trash_pixmap))
        self.trash_button.setIconSize(trash_pixmap.size())
        self.trash_button.setFixedSize(24, 24)
        self.trash_button.setStyleSheet("border: none; background: transparent;")
        self.trash_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.trash_button.clicked.connect(self.confirm_delete)

        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.trash_button)
        self.layout.addLayout(top_layout)

        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)

    def confirm_delete(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Удалить плитку", f"Вы уверены, что хотите удалить плитку '{self.text_label.text()}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_tile()

    def delete_tile(self):
        self.setParent(None)
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"Выбрано устройство: {self.text_label.text()}")

class AssistantUI(QMainWindow):
    def __init__(self):
        super().__init__()
        font = QApplication.font()
        font.setFamily("Arial")
        QApplication.setFont(font)
        self.assistant = VoiceAssistant()
        self.assistant.stopped.connect(self.on_assistant_stopped)
        self.assistant.state_changed.connect(self.on_assistant_state_changed)
        self.init_ui()
        self.start_assistant()

    def start_assistant(self):
        print("start_assistant started")
        self.thread = QThread()
        self.assistant.moveToThread(self.thread)
        self.thread.started.connect(self.assistant.start)
        self.thread.start()
        self.btn_start_assistant.hide()
        print("start_assistant completed")

    def on_assistant_stopped(self):
        print("on_assistant_stopped called")
        self.btn_start_assistant.show()

    def on_assistant_state_changed(self, is_active):
        if is_active:
            self.face_widget.start_animation()
        else:
            self.face_widget.stop_animation()

    def init_ui(self):
        print("init_ui started")
        self.setWindowTitle("Mika Assistant")
        self.setGeometry(300, 300, 800, 600)
        self.setStyleSheet("QMainWindow { background-color: #1A1A1A; color: white; }")

        self.stacked_widget = QStackedWidget()
        self.main_page = self.create_main_page()
        self.settings_page = QWidget()
        self.settings_stacked = QStackedWidget()
        self.settings_page_layout = QVBoxLayout(self.settings_page)
        self.settings_page_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_page_layout.addWidget(self.settings_stacked)

        self.settings_tab = self.create_settings_page()
        self.devices_tab = self.create_devices_page()
        self.bulb_settings_tab = self.create_bulb_settings_page()
        self.phone_settings_tab = self.create_phone_settings_page()  # Новая вкладка для телефона

        self.settings_stacked.addWidget(self.settings_tab)
        self.settings_stacked.addWidget(self.devices_tab)
        self.settings_stacked.addWidget(self.bulb_settings_tab)
        self.settings_stacked.addWidget(self.phone_settings_tab)

        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        self.setCentralWidget(self.stacked_widget)
        print("init_ui completed")

    def create_devices_page(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #1A1A1A;")
        main_layout = QVBoxLayout(widget)

        search_layout = QHBoxLayout()
        self.device_search_input = QLineEdit()
        self.device_search_input.setPlaceholderText("Поиск по имени устройства...")
        self.device_search_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; }")
        self.device_search_input.textChanged.connect(self.filter_devices)
        search_layout.addWidget(self.device_search_input)

        self.btn_add_tile = QPushButton("+")
        self.btn_add_tile.setFixedSize(30, 30)
        self.btn_add_tile.setStyleSheet("""
            QPushButton {
                background-color: #2E2E2E;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
            }
        """)
        self.btn_add_tile.clicked.connect(self.open_add_tile_dialog)
        search_layout.addWidget(self.btn_add_tile)

        main_layout.addLayout(search_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1A1A1A; border: none; }")
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.bulb_tile = DeviceTile("Лампочка KOJIMA e27", "fotos/kojima_lamb.PNG", self)
        original_mousePressEvent = self.bulb_tile.mousePressEvent
        def new_mousePressEvent(event):
            self.open_bulb_settings(event)
            original_mousePressEvent(event)
        self.bulb_tile.mousePressEvent = new_mousePressEvent
        self.scroll_layout.addWidget(self.bulb_tile)

        self.mobile_tile = DeviceTile("Мой телефон", "fotos/mobile.PNG", self)
        original_phone_mousePressEvent = self.mobile_tile.mousePressEvent
        def new_phone_mousePressEvent(event):
            self.open_phone_settings(event)
            original_phone_mousePressEvent(event)
        self.mobile_tile.mousePressEvent = new_phone_mousePressEvent
        self.scroll_layout.addWidget(self.mobile_tile)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        nav_button_style = """
            QPushButton { background-color: #2E2E2E; color: white; border: none; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #3E3E3E; }
        """
        btn_back = QPushButton("Назад")
        btn_back.setStyleSheet(nav_button_style)
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        main_layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignBottom)

        return widget

    def open_add_tile_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить новую плитку")
        dialog.setFixedSize(300, 150)
        dialog.setStyleSheet("background-color: black; color: white;")

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        layout.addRow("Название:", name_input)

        photo_input = QLineEdit()
        layout.addRow("Путь к фото:", photo_input)

        def browse_photo():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
            if file_path:
                photo_input.setText(file_path)

        browse_button = QPushButton("Обзор")
        browse_button.clicked.connect(browse_photo)
        layout.addRow("", browse_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.add_new_tile(name_input.text(), photo_input.text(), dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.exec()

    def add_new_tile(self, name, photo_path, dialog):
        if not name or not photo_path:
            return
        new_tile = DeviceTile(name, photo_path, self)
        self.scroll_layout.addWidget(new_tile)
        dialog.accept()

    def open_bulb_settings(self, event):
        self.settings_stacked.setCurrentWidget(self.bulb_settings_tab)

    def open_phone_settings(self, event):
        self.settings_stacked.setCurrentWidget(self.phone_settings_tab)

    def filter_devices(self, text):
        text = text.lower()
        for tile in self.findChildren(DeviceTile):
            if text in tile.text_label.text().lower():
                tile.show()
            else:
                tile.hide()

    def create_bulb_settings_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        nav_button_style = """
            QPushButton { background-color: #1A1A1A; color: white; border: none; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #2E2E2E; }
        """

        btn_back = QPushButton("Назад")
        btn_back.setStyleSheet(nav_button_style)
        btn_back.clicked.connect(lambda: self.settings_stacked.setCurrentWidget(self.devices_tab))

        device_id_layout = QVBoxLayout()
        device_id_label = QLabel("Лампочка DEVICE_ID:")
        device_id_label.setStyleSheet("color: white; font-size: 14px;")
        self.bulb_device_id_input = QLineEdit(getattr(self.assistant, 'device_id', ''))
        self.bulb_device_id_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; border: 1px solid #444; }")
        device_id_layout.addWidget(device_id_label)
        device_id_layout.addWidget(self.bulb_device_id_input)

        layout.addLayout(device_id_layout)
        layout.addStretch()
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignBottom)

        return widget

    def create_phone_settings_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        nav_button_style = """
            QPushButton { background-color: #1A1A1A; color: white; border: none; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #2E2E2E; }
        """

        btn_back = QPushButton("Назад")
        btn_back.setStyleSheet(nav_button_style)
        btn_back.clicked.connect(lambda: self.settings_stacked.setCurrentWidget(self.devices_tab))

        phone_ip_layout = QVBoxLayout()
        phone_ip_label = QLabel("IP-адрес телефона:")
        phone_ip_label.setStyleSheet("color: white; font-size: 14px;")
        self.phone_ip_input = QLineEdit(getattr(self.assistant, 'phone_ip', ''))
        self.phone_ip_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; border: 1px solid #444; }")
        phone_ip_layout.addWidget(phone_ip_label)
        phone_ip_layout.addWidget(self.phone_ip_input)

        phone_token_layout = QVBoxLayout()
        phone_token_label = QLabel("Токен телефона:")
        phone_token_label.setStyleSheet("color: white; font-size: 14px;")
        self.phone_token_input = QLineEdit(getattr(self.assistant, 'phone_token', ''))
        self.phone_token_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; border: 1px solid #444; }")
        phone_token_layout.addWidget(phone_token_label)
        phone_token_layout.addWidget(self.phone_token_input)

        layout.addLayout(phone_ip_layout)
        layout.addLayout(phone_token_layout)
        layout.addStretch()
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignBottom)

        return widget

    def create_main_page(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        nav_layout.setContentsMargins(0, 0, 10, 0)
        
        nav_button_style = """
            QPushButton { background-color: #1A1A1A; color: white; border: none; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #2E2E2E; }
        """
        
        self.btn_settings = QPushButton("Настройки")
        self.btn_settings.setStyleSheet(nav_button_style)
        self.btn_settings.clicked.connect(lambda: [self.stacked_widget.setCurrentIndex(1), self._switch_settings_tab("settings")])
        
        self.btn_devices = QPushButton("Устройства")
        self.btn_devices.setStyleSheet(nav_button_style)
        self.btn_devices.clicked.connect(lambda: [self.stacked_widget.setCurrentIndex(1), self._switch_settings_tab("devices")])
        
        nav_layout.addWidget(self.btn_settings)
        nav_layout.addWidget(self.btn_devices)
        
        main_layout.addLayout(nav_layout)
        
        self.face_widget = FaceWidget()
        main_layout.addWidget(self.face_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btn_start_assistant = QPushButton("Включить Мику")
        self.btn_start_assistant.setStyleSheet(nav_button_style)
        self.btn_start_assistant.clicked.connect(self.restart_assistant)
        self.btn_start_assistant.hide()
        main_layout.addWidget(self.btn_start_assistant, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return widget

    def _switch_settings_tab(self, tab_name):
        if tab_name == "settings":
            self.settings_stacked.setCurrentIndex(0)
        elif tab_name == "devices":
            self.settings_stacked.setCurrentIndex(1)
        elif tab_name == "bulb_settings":
            self.settings_stacked.setCurrentIndex(2)
        elif tab_name == "phone_settings":
            self.settings_stacked.setCurrentIndex(3)

    def restart_assistant(self):
        print("restart_assistant called")
        if hasattr(self, 'thread') and self.thread.isRunning():
            try:
                self.thread.started.disconnect()
            except Exception:
                pass
            self.thread.quit()
            self.thread.wait()
        print("Перезапуск ассистента: создаём новый поток и ассистента")
        self.thread = QThread()
        self.assistant = VoiceAssistant()
        self.assistant.stopped.connect(self.on_assistant_stopped)
        self.assistant.state_changed.connect(self.on_assistant_state_changed)
        self.assistant.moveToThread(self.thread)
        self.thread.started.connect(self.assistant.start)
        self.thread.start()
        self.btn_start_assistant.hide()

    def _populate_devices(self, combobox, is_input=True):
        combobox.clear()
        saved_index = self.assistant.selected_mic if is_input else self.assistant.selected_speaker
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if (is_input and dev['max_input_channels'] > 0) or (not is_input and dev['max_output_channels'] > 0):
                    name = dev['name']
                    combobox.addItem(name, userData=i)
                    if i == saved_index:
                        combobox.setCurrentIndex(combobox.count()-1)
        except Exception as e:
            print(f"Ошибка при получении устройств: {str(e)}")

    def create_settings_page(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        nav_button_style = """
            QPushButton { background-color: #1A1A1A; color: white; border: none; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #2E2E2E; }
        """
        
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)
        
        mic_layout = QVBoxLayout()
        mic_label = QLabel("Выберите микрофон:")
        mic_label.setStyleSheet("color: white; font-size: 14px;")
        self.mic_combobox = QComboBox()
        self.mic_combobox.setStyleSheet("QComboBox { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; }")
        self._populate_devices(self.mic_combobox, is_input=True)
        mic_layout.addWidget(mic_label)
        mic_layout.addWidget(self.mic_combobox)
        
        api_layout = QVBoxLayout()
        api_label = QLabel("API ключ нейросети:")
        api_label.setStyleSheet("color: white; font-size: 14px;")
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; border: 1px solid #444; }")
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_input)
        
        speaker_layout = QVBoxLayout()
        speaker_label = QLabel("Выберите динамики:")
        speaker_label.setStyleSheet("color: white; font-size: 14px;")
        self.speaker_combobox = QComboBox()
        self.speaker_combobox.setStyleSheet("QComboBox { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; }")
        self._populate_devices(self.speaker_combobox, is_input=False)
        speaker_layout.addWidget(speaker_label)
        speaker_layout.addWidget(self.speaker_combobox)
        
        token_layout = QVBoxLayout()
        token_label = QLabel("Токен управления ACCESS_TOKEN:")
        token_label.setStyleSheet("color: white; font-size: 14px;")
        self.token_input = QLineEdit(getattr(self.assistant, 'access_token', ''))
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet("QLineEdit { background-color: #2E2E2E; color: white; padding: 8px; border-radius: 4px; border: 1px solid #444; }")
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        
        sensitivity_layout = QVBoxLayout()
        sensitivity_label = QLabel("Чувствительность микрофона:")
        sensitivity_label.setStyleSheet("color: white; font-size: 14px;")
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 100)
        self.sensitivity_slider.setValue(int(getattr(self.assistant, 'silence_threshold', 0.2) * 100))
        self.sensitivity_slider.setStyleSheet("QSlider { background-color: #2E2E2E; }")
        self.sensitivity_value_label = QLabel(f"{getattr(self.assistant, 'silence_threshold', 0.2):.2f}")
        self.sensitivity_value_label.setStyleSheet("color: white;")
        
        self.sensitivity_slider.valueChanged.connect(self._update_sensitivity_label)
        sensitivity_layout.addWidget(sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_value_label)
        
        music_sensitivity_layout = QVBoxLayout()
        music_sensitivity_label = QLabel("Чувствительность режима музыки:")
        music_sensitivity_label.setStyleSheet("color: white; font-size: 14px;")
        self.music_sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.music_sensitivity_slider.setRange(1, 1000)
        default_music_sensitivity = 10
        if hasattr(self.assistant, 'music_mode') and hasattr(self.assistant.music_mode, 'sensitivity_threshold'):
            default_music_sensitivity = int(self.assistant.music_mode.sensitivity_threshold * 100000)
        self.music_sensitivity_slider.setValue(default_music_sensitivity)
        self.music_sensitivity_slider.setStyleSheet("QSlider { background-color: #2E2E2E; }")
        self.music_sensitivity_value_label = QLabel(f"{default_music_sensitivity / 100000:.5f}")
        self.music_sensitivity_value_label.setStyleSheet("color: white;")
        self.music_sensitivity_slider.valueChanged.connect(self._update_music_sensitivity_label)
        music_sensitivity_layout.addWidget(music_sensitivity_label)
        music_sensitivity_layout.addWidget(self.music_sensitivity_slider)
        music_sensitivity_layout.addWidget(self.music_sensitivity_value_label)
        
        settings_layout.addLayout(mic_layout)
        settings_layout.addLayout(speaker_layout)
        settings_layout.addLayout(api_layout)
        settings_layout.addLayout(token_layout)
        settings_layout.addLayout(sensitivity_layout)
        settings_layout.addLayout(music_sensitivity_layout)
        settings_layout.addStretch()
        
        btn_back = QPushButton("Назад")
        btn_back.setStyleSheet(nav_button_style)
        btn_back.clicked.connect(lambda: [self.stacked_widget.setCurrentIndex(0), self.save_settings()])
        
        main_layout.addLayout(settings_layout)
        main_layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        
        api_key = getattr(self.assistant, 'api_key', '')
        self.api_input.setText(api_key)
        return widget

    def _update_sensitivity_label(self, value):
        self.sensitivity_value_label.setText(f"{value / 100:.2f}")

    def _update_music_sensitivity_label(self, value):
        self.music_sensitivity_value_label.setText(f"{value / 100000:.5f}")

    def save_settings(self):
        pass

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    print("Application starting")
    app = QApplication(sys.argv)
    window = AssistantUI()
    window.show()
    print("Window shown")
    sys.exit(app.exec())