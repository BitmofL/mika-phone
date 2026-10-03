import os
from plyer import notification
from .command import Command

def shutdown_computer():
    """Инициировать выключение компьютера через 5 секунд."""
    os.system("shutdown /s /t 5")

def show_shutdown_confirmation():
    """Показать уведомление Windows для подтверждения выключения."""
    notification.notify(
        title="Подтверждение выключения",
        message="Вы уверены, что хотите выключить компьютер? Скажите 'да' или 'нет'.",
        app_name="Mika Assistant",
        timeout=10
    )

class ShutdownHandler:
    def __init__(self, light_control):
        self.light_control = light_control

    def initiate_shutdown(self):
        print("Вы уверены? Скажите 'да' или 'нет'...")
        self.light_control.stop_breathing()
        show_shutdown_confirmation()

    def handle_confirmation(self, text, assistant):
        text_lower = text.lower()
        if any(word in text_lower for word in ["да", "ага", "конечно", "давай", "ок", "окей"]):
            print("Выключение компьютера...")
            shutdown_computer()
            assistant.stop()
            return None
        else:
            cancel_words = ["нет", "не", "отмена", "стоп", "не надо", "не нужно"]
            if any(word in text_lower.split() for word in cancel_words):
                print("Отмена выключения.")
                return None
            else:
                print("Скажите 'да' или 'нет'.")
                return "shutdown"

class ShutdownCommand(Command):
    def should_handle(self, text):
        return "выключись" in text.lower()

    def execute(self, text, assistant):
        print("Выключаюсь...")
        assistant.light_control.stop_breathing()
        assistant.music_mode.stop_music_mode()
        assistant.stop()
        return {'response': "Ассистент выключен", 'confirmation': None}

class ComputerShutdownCommand(Command):
    def should_handle(self, text):
        return any(x in text.lower() for x in ["выключи компьютер", "выключи пк", "выключи комп"])

    def execute(self, text, assistant):
        assistant.shutdown_handler.initiate_shutdown()
        return {'response': "Подтвердите выключение", 'confirmation': assistant.shutdown_handler}