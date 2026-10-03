from . import control_kojima_bulb as bulb_control
import threading
import time
import os
from .command import Command
import re

class LightControl:
    def __init__(self, access_token, device_id):
        self.access_token = access_token
        self.device_id = device_id
        self._breathing_active = False
        self.previous_state = None
        self.color_map = {
            "красный": {"h": 0, "s": 100, "v": 100},
            "синий": {"h": 240, "s": 100, "v": 100},
            "жёлтый": {"h": 50, "s": 100, "v": 100},
            "зелёный": {"h": 120, "s": 100, "v": 100},
            "фиолетовый": {"h": 270, "s": 100, "v": 100},
            "оранжевый": {"h": 30, "s": 100, "v": 100},
            "белый": {"temperature_k": 6500},
            "бирюзовый": {"h": 180, "s": 100, "v": 100},
            "голубой": {"h": 210, "s": 100, "v": 100},
            "ярко зелёный": {"h": 145, "s": 100, "v": 100}
        }

    def is_breathing_active(self):
        return self._breathing_active

    def handle_command(self, text, assistant):
        text = text.lower()
        if "отмена" in text or "выключи режим" in text:
            if self.is_breathing_active():
                self.stop_breathing()
                print("Режим дыхания остановлен.")
                return None, 0
            elif assistant.music_mode.is_running:
                assistant.music_mode.stop_music_mode()
                print("Режим музыки остановлен.")
                return None, 0
            else:
                print("Нет активных режимов для отключения.")
                return None, 0
        elif "включи свет" in text:
            print("Включение света...")
            self.stop_breathing()
            bulb_control.turn_on(self.access_token)
            return None, 0
        elif "выключи свет" in text:
            print("Выключение света...")
            self.stop_breathing()
            bulb_control.turn_off(self.access_token)
            return None, 0
        elif "сделай свет теплее" in text:
            print("Установка теплого света (2700K)...")
            self.stop_breathing()
            bulb_control.set_temperature(self.access_token, 2700)
            return None, 0
        elif "сделай свет холоднее" in text:
            print("Установка холодного света (6500K)...")
            self.stop_breathing()
            bulb_control.set_temperature(self.access_token, 6500)
            return None, 0
        elif "яркость" in text and ("процентов" in text or "процента" in text):
            brightness = self._extract_brightness(text)
            if brightness is not None:
                print(f"Установка яркости: {brightness}%...")
                self.stop_breathing()
                bulb_control.set_brightness(self.access_token, brightness)
                return None, 0
            else:
                print("Не удалось распознать уровень яркости.")
                return None, 0
        elif any(phrase in text for phrase in ["режим дыхания", "режим дыханиe", "режим дыханья", "режим дыханье"]):
            print("Запуск режима дыхания...")
            self.breathing_effect()
            return None, 0
        elif "цвет" in text:
            color_match = re.search(r"цвет\s+([\w\s]+)", text)
            if color_match:
                color_name = color_match.group(1).strip()
                if color_name in self.color_map:
                    color = self.color_map[color_name]
                    self.stop_breathing()
                    if "temperature_k" in color:
                        print(f"Установка цвета: {color_name} (Температура: {color['temperature_k']}K)...")
                        bulb_control.set_temperature(self.access_token, color["temperature_k"])
                    else:
                        print(f"Установка цвета: {color_name} (HSV: h={color['h']}, s={color['s']}, v={color['v']})...")
                        bulb_control.set_hsv_color(self.access_token, color)
                else:
                    print(f"Неизвестный цвет: {color_name}")
            else:
                print(f"Не удалось распознать цвет в команде: {text}")
            return None, 0
        else:
            print(f"Команда не распознана: {text}")
            return None, 0

    def _extract_brightness(self, text):
        number_map = {
            "ноль": 0, "один": 1, "два": 2, "три": 3, "четыре": 4,
            "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
            "десять": 10, "двадцать": 20, "тридцать": 30, "сорок": 40,
            "пятьдесят": 50, "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80,
            "девяносто": 90, "сто": 100
        }
        words = text.split()
        for i, word in enumerate(words):
            if word in number_map:
                if i + 1 < len(words) and words[i + 1] in number_map:
                    return min(number_map[words[i]] + number_map[words[i + 1]], 100)
                return number_map[word]
            elif word.isdigit():
                return int(word)
        return None

    def breathing_effect(self):
        if self._breathing_active:
            print("Режим дыхания уже запущен")
            return
        
        self.previous_state = bulb_control.get_device_state(self.access_token, self.device_id)
        if self.previous_state:
            for cap in self.previous_state:
                if cap["type"] == "devices.capabilities.on_off" and not cap["state"]["value"]:
                    print("Лампочка выключена, пытаюсь включить...")
                    bulb_control.turn_on(self.access_token)
                    break

        def run_breathing():
            brightness_min = 1
            brightness_max = 100
            step = 0.5
            brightness = brightness_min
            increasing = True
            sleep_time = 0.05

            print("Поток дыхания запущен")
            while self._breathing_active:
                bulb_control.set_brightness(self.access_token, int(brightness))
                if brightness == brightness_max or brightness == brightness_min:
                    for _ in range(30):
                        if not self._breathing_active:
                            break
                        time.sleep(0.1)
                else:
                    time.sleep(sleep_time)

                if increasing:
                    brightness += step
                    if brightness >= brightness_max:
                        brightness = brightness_max
                        increasing = False
                else:
                    brightness -= step
                    if brightness <= brightness_min:
                        brightness = brightness_min
                        increasing = True

            print("Поток дыхания завершен")

        self._breathing_active = True
        thread = threading.Thread(target=run_breathing, daemon=True)
        thread.start()
        self._breathing_thread = thread

    def stop_breathing(self):
        if not self._breathing_active:
            print("Режим дыхания не активен")
            return
        self._breathing_active = False
        if hasattr(self, "_breathing_thread") and self._breathing_thread.is_alive():
            print("Ожидание завершения потока дыхания...")
            self._breathing_thread.join(timeout=5)
            if self._breathing_thread.is_alive():
                print("Поток дыхания не завершился в течение 5 секунд")
            else:
                print("Поток дыхания остановлен")
        if self.previous_state:
            bulb_control.restore_device_state(self.access_token, self.device_id, self.previous_state)
            self.previous_state = None

class LightControlCommand(Command):
    def should_handle(self, text):
        keywords = ["свет", "яркость", "цвет", "режим", "лампочка"]
        return any(keyword in text for keyword in keywords)

    def execute(self, text, assistant):
        awaiting_confirmation, _ = assistant.light_control.handle_command(text, assistant)
        if awaiting_confirmation:
            return {'response': "Ожидание подтверждения", 'confirmation': awaiting_confirmation}
        return {'response': "Команда выполнена", 'confirmation': None}

class StopBreathingCommand(Command):
    def should_handle(self, text):
        text = text.lower()
        print(f"Checking if should handle: {text}")
        return (
            re.search(r'\bрежим\b', text, re.IGNORECASE) is not None 
            and re.search(r'\bдыхан[а-яё]*\b', text, re.IGNORECASE) is not None
        )

    def execute(self, text, assistant):
        print("Executing StopBreathingCommand")
        assistant.light_control.stop_breathing()
        return {'response': "Режим дыхания остановлен", 'confirmation': None}