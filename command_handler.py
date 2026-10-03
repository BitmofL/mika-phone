import importlib
import os
import requests
import commands.light_control
import commands.computer_control
import commands.music_mode
import commands.phone_control  # Новый импорт
from commands.command import Command

class CommandHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self.commands = [
            commands.music_mode.MusicModeCommand(),
            commands.light_control.LightControlCommand(),
            commands.computer_control.ShutdownCommand(),
            commands.computer_control.ComputerShutdownCommand(),
            commands.light_control.StopBreathingCommand(),
            commands.phone_control.PhoneControlCommand(),  # Новая команда
        ] + self._load_commands()

    def _load_commands(self):
        """Динамическая загрузка команд из папки commands."""
        commands = []
        command_modules = ['volume', 'browser_command', 'system_folders']
        for module_name in command_modules:
            try:
                module = importlib.import_module(f'commands.{module_name}')
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if isinstance(obj, type) and issubclass(obj, Command) and obj != Command:
                        commands.append(obj())
            except Exception as e:
                print(f"Ошибка загрузки {module_name}: {str(e)}")
        return commands

    def handle(self, text, assistant):
        """Обработка текста через список команд."""
        for cmd in self.commands:
            if cmd.should_handle(text):
                return cmd.execute(text, assistant)
        return {'response': "Команда не распознана", 'confirmation': None}

    def control_device(self, action, value=None):
        """Управление устройством через Yandex Smart Home API"""
        url = f"https://api.iot.yandex.net/v1.0/devices/{self.assistant.device_id}/actions"
        headers = {
            "Authorization": f"Bearer {self.assistant.access_token}",
            "Content-Type": "application/json"
        }
        if action == "devices.capabilities.on_off":
            payload = {
                "actions": [{
                    "type": action,
                    "state": {"instance": "on", "value": value}
                }]
            }
        elif action == "devices.capabilities.color_setting":
            payload = {
                "actions": [{
                    "type": action,
                    "state": {"instance": "hsv", "value": value}
                }]
            }
        else:
            return "Неподдерживаемое действие"

        print(f"Отправка запроса: {payload}")
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return "Устройство успешно управляется"
        except requests.RequestException as e:
            error_message = f"Ошибка управления устройством: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_message += f"\nОтвет сервера: {e.response.text}"
            return error_message