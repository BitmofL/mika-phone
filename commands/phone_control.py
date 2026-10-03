import requests
import os
import re
from .command import Command
import win32gui
import win32con

class PhoneControl:
    def __init__(self, phone_ip, phone_token):
        self.phone_ip = phone_ip
        self.phone_token = phone_token
        self.base_url = f"http://{self.phone_ip}:5000"  # Предполагаемый адрес сервера на телефоне

    def find_phone(self):
        """Отправляет запрос на телефон для воспроизведения звука."""
        try:
            response = requests.post(
                f"{self.base_url}/find",
                headers={"Authorization": f"Bearer {self.phone_token}"}
            )
            response.raise_for_status()
            return "Телефон издает звук для поиска."
        except requests.RequestException as e:
            return f"Ошибка при поиске телефона: {str(e)}"

    def open_app(self, app_name):
        """Отправляет запрос на открытие приложения на телефоне."""
        try:
            response = requests.post(
                f"{self.base_url}/open_app",
                json={"app_name": app_name},
                headers={"Authorization": f"Bearer {self.phone_token}"}
            )
            response.raise_for_status()
            return f"Открываю {app_name} на телефоне."
        except requests.RequestException as e:
            return f"Ошибка при открытии приложения: {str(e)}"

    def send_files(self):
        """Отправляет выделенные файлы из проводника на телефон."""
        hwnd = win32gui.GetForegroundWindow()
        if "Explorer" not in win32gui.GetWindowText(hwnd):
            return "Пожалуйста, выделите файлы в проводнике."

        import win32clipboard
        win32clipboard.OpenClipboard()
        files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
        win32clipboard.CloseClipboard()

        if not files:
            return "Файлы не выделены."

        try:
            with requests.Session() as session:
                for file_path in files:
                    with open(file_path, 'rb') as f:
                        response = session.post(
                            f"{self.base_url}/upload",
                            files={"file": (os.path.basename(file_path), f)},
                            headers={"Authorization": f"Bearer {self.phone_token}"}
                        )
                        response.raise_for_status()
            return "Файлы успешно отправлены на телефон."
        except requests.RequestException as e:
            return f"Ошибка при отправке файлов: {str(e)}"

class PhoneControlCommand(Command):
    def should_handle(self, text):
        keywords = ["телефон", "найди", "открой", "отправь", "файл"]
        return any(keyword in text.lower() for keyword in keywords)

    def execute(self, text, assistant):
        text = text.lower()
        phone_control = PhoneControl(assistant.phone_ip, assistant.phone_token)

        if "найди телефон" in text:
            response = phone_control.find_phone()
            return {'response': response, 'confirmation': None}
        
        elif "открой" in text:
            app_match = re.search(r"открой\s+(.+?)\s+на\s+телефоне", text)
            if app_match:
                app_name = app_match.group(1)
                response = phone_control.open_app(app_name)
                return {'response': response, 'confirmation': None}
            return {'response': "Укажите название приложения.", 'confirmation': None}
        
        elif "отправь файл" in text:
            response = phone_control.send_files()
            return {'response': response, 'confirmation': None}
        
        return {'response': "Команда для телефона не распознана.", 'confirmation': None}