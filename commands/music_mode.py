import time
import numpy as np
import sounddevice as sd
from plyer import notification
import random
from . import control_kojima_bulb as bulb_control
from vosk import Model, KaldiRecognizer
import pyaudio
import json
from .command import Command
import re

class MusicMode:
    def __init__(self, access_token, device_id, sample_rate=16000, reaction_speed=0.1, model_path=None):
        import os
        if model_path is None:
            model_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "vosk-model-small-ru-0.22"))
        self.access_token = access_token
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.reaction_speed = reaction_speed
        self.is_running = False
        self.hsv_colors = [
            {"h": 0, "s": 100, "v": 100},   # Красный
            {"h": 120, "s": 100, "v": 100}, # Зелёный
            {"h": 240, "s": 100, "v": 100}, # Синий
            {"h": 60, "s": 100, "v": 100},  # Жёлтый
            {"h": 180, "s": 100, "v": 100}, # Бирюзовый
            {"h": 270, "s": 100, "v": 100}  # Фиолетовый
        ]
        self.model = Model(model_path)
        grammar = '["мика", "компьютер", "комната", "отмена", "выключи режим", "выключи музыку"]'
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.previous_state = None

    def set_sensitivity_threshold(self, threshold):
        self.reaction_speed = threshold

    def show_source_selection(self):
        notification.notify(
            title="Режим музыки",
            message="Слушать ритм на компьютере или в вашей комнате? Скажите 'компьютер', 'комната' или 'отмена'.",
            app_name="Mika Assistant",
            timeout=10
        )

    def analyze_audio(self, indata, frames, time, status):
        if status:
            print(status)
        rms = np.sqrt(np.mean(indata**2))
        if rms > 0.05:
            color = random.choice(self.hsv_colors)
            bulb_control.set_hsv_color(self.access_token, color)

    def start_music_mode(self, source="mic", device_index=None):
        self.is_running = True
        print(f"Запуск режима музыки ({source})...")
        try:
            self.previous_state = bulb_control.get_device_state(self.access_token, self.device_id)
            if self.previous_state:
                for cap in self.previous_state:
                    if cap["type"] == "devices.capabilities.on_off" and not cap["state"]["value"]:
                        bulb_control.turn_on(self.access_token)
                        break

            device_idx = None
            if source == "pc":
                device_idx = None
                devices = self.p.get_device_count()
                for i in range(devices):
                    dev_info = self.p.get_device_info_by_index(i)
                    if 'стерео микшер' in dev_info['name'].lower() or 'stereo mix' in dev_info['name'].lower():
                        if dev_info.get('maxInputChannels', 0) > 0:
                            device_idx = i
                            print(f"Найдено устройство для захвата звука: {dev_info['name']} (index: {device_idx})")
                            break
                if device_idx is None:
                    print("Устройство для захвата системного звука не найдено. Используется микрофон.")
                    device_idx = None
            else:
                device_idx = None

            channels = 1
            if device_idx is not None:
                dev_info = self.p.get_device_info_by_index(device_idx)
                max_input_channels = dev_info.get('maxInputChannels', 1)
                if max_input_channels > 0:
                    channels = max_input_channels
                print(f"Используем количество каналов: {channels} для устройства {dev_info['name']}")
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=2048,
                input_device_index=device_idx
            )

            while self.is_running:
                data = self.stream.read(2048, exception_on_overflow=False)
                self.analyze_audio(np.frombuffer(data, dtype=np.int16), 2048, None, None)
                self.recognizer.AcceptWaveform(data)
                result = json.loads(self.recognizer.PartialResult())
                recognized_text = result.get('partial', '')
                if "мика" in recognized_text.lower():
                    print("Обнаружено 'Мика' в режиме музыки. Ожидание команды...")
                    self._handle_music_mode_command()
                time.sleep(self.reaction_speed)
        except Exception as e:
            print(f"Ошибка в режиме музыки: {e}")
        finally:
            self.is_running = False
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            if self.previous_state:
                bulb_control.restore_device_state(self.access_token, self.device_id, self.previous_state)
            print("Режим музыки остановлен.")

    def _handle_music_mode_command(self):
        command_buffer = b''
        start_time = time.time()
        timeout = 5
        while time.time() - start_time < timeout and self.is_running:
            try:
                data = self.stream.read(2048, exception_on_overflow=False)
                command_buffer += data
                if len(command_buffer) > 16000:
                    if self.recognizer.AcceptWaveform(command_buffer):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '')
                        print(f"Распознанная команда в режиме музыки: {text}")
                        text_lower = text.lower()
                        if "отмена" in text_lower or "выключи режим" in text_lower:
                            print("Отключение режима музыки...")
                            self.stop_music_mode()
                        elif "выключи музыку" in text_lower:
                            print("Пауза музыки и выход из режима...")
                            self.stop_music_mode()
                        elif "компьютер" in text_lower:
                            print("Переключение на источник звука с компьютера...")
                            self.stop_music_mode()
                            self.start_music_mode(source="pc")
                    command_buffer = b''
            except Exception as e:
                print(f"Ошибка при обработке команды в режиме музыки: {e}")
                break

    def stop_music_mode(self):
        self.is_running = False
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None  # Убедимся, что поток очищается
        if self.previous_state:
            bulb_control.restore_device_state(self.access_token, self.device_id, self.previous_state)
            self.previous_state = None  # Сброс предыдущего состояния
        print("Режим музыки остановлен.")

    def initiate_music_mode(self, light_control):
        print("Слушать ритм на компьютере или в вашей комнате? Скажите 'компьютер', 'комната' или 'отмена'...")
        light_control.stop_breathing()
        self.show_source_selection()

    def handle_confirmation(self, text, assistant):
        text_lower = text.lower()
        if any(word in text_lower for word in ["компьютер", "компьютэр"]):
            print("Запуск режима музыки для звука с компьютера...")
            self.start_music_mode(source="pc", device_index=assistant.selected_speaker)
            return None
        elif "комната" in text_lower:
            print("Запуск режима музыки для звука в комнате...")
            self.start_music_mode(source="mic")
            return None
        elif "отмена" in text_lower:
            print("Отмена режима музыки.")
            return None
        else:
            print("Скажите 'компьютер', 'комната' или 'отмена'.")
            return "music_mode"

import re

class MusicModeCommand(Command):
    def should_handle(self, text):
        text = text.lower()
        # Проверяем наличие "режим" и слова, начинающегося с "музык"
        return "режим" in text and re.search(r'\bмузык\w*\b', text) is not None
        
    def execute(self, text, assistant):
        assistant.music_mode.initiate_music_mode(assistant.light_control)
        return {'response': "Выберите источник звука", 'confirmation': assistant.music_mode}