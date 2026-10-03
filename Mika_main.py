from vosk import Model, KaldiRecognizer
import pyaudio
import json
import queue
import time
import numpy as np
import commands.control_kojima_bulb as bulb_control
import commands.computer_control
import commands.music_mode
import commands.light_control
import commands.phone_control
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from command_handler import CommandHandler

class AudioProcessor(QThread):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self._running = True

    def run(self):
        self.assistant._process_audio()

    def stop(self):
        self._running = False
        self.quit()
        self.wait()

class VoiceAssistant(QObject):
    stopped = pyqtSignal()
    state_changed = pyqtSignal(bool)
    CONFIG_FILE = "settings.json"

    def __init__(self, model_path="vosk-model-small-ru-0.22"):
        super().__init__()
        if model_path == "vosk-model-small-ru-0.22":
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), model_path))
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("Модель Vosk загружена успешно.")
        except Exception as e:
            print(f"Ошибка при загрузке модели Vosk: {e}")
            exit(1)
        
        self.activation_phrases = ["мика", "мико", "мику", "мике"]
        self.is_activated = False
        self.audio_queue = queue.Queue()
        self.last_activity_time = 0
        self.command_timeout = 5
        self.silence_threshold = 5
        self.expecting_command = False

        self.p = pyaudio.PyAudio()
        self.selected_mic = self._find_device_index_by_name("Microphone (fifine Microphone)", input=True)
        self.selected_speaker = self._find_device_index_by_name("P27FBA-RX (NVIDIA High Definition Audio)", input=False)

        self.load_settings()  # Загружаем настройки при инициализации

        self.device_id = bulb_control.DEVICE_ID
        self.access_token = bulb_control.ACCESS_TOKEN
        self.music_mode = commands.music_mode.MusicMode(self.access_token, self.device_id)
        self.light_control = commands.light_control.LightControl(self.access_token, self.device_id)
        self.shutdown_handler = commands.computer_control.ShutdownHandler(self.light_control)
        self.command_handler = CommandHandler(self)
        self.stream = self._init_audio_stream()

        self.audio_thread = AudioProcessor(self)
        self.awaiting_confirmation = None
        self.confirmation_handler = None
        self.confirmation_start_time = 0
        self.confirmation_timeout = 10

    def load_settings(self):
        """Загрузка настроек из файла settings.json."""
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.selected_mic = data.get("mic_index", 1)
                self.selected_speaker = data.get("speaker_index", 20)
                self.device_id = data.get("device_id", "")
                self.access_token = data.get("access_token", "")
                self.silence_threshold = data.get("silence_threshold", 5)
                self.phone_ip = data.get("phone_ip", "")  # Новое поле
                self.phone_token = data.get("phone_token", "")  # Новое поле
        except FileNotFoundError:
            print("Файл настроек не найден, используются значения по умолчанию.")
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")

    def update_settings(self, mic_index, speaker_index, device_id, access_token, silence_threshold, phone_ip=None, phone_token=None):
        self.selected_mic = mic_index
        self.selected_speaker = speaker_index
        self.device_id = device_id
        self.access_token = access_token
        self.silence_threshold = silence_threshold
        if phone_ip is not None:
            self.phone_ip = phone_ip
        if phone_token is not None:
            self.phone_token = phone_token
        self._save_settings()
        self._restart_stream()

    def _save_settings(self):
        data = {
            "mic_index": self.selected_mic,
            "speaker_index": self.selected_speaker,
            "device_id": self.device_id,
            "access_token": self.access_token,
            "silence_threshold": self.silence_threshold,
            "phone_ip": getattr(self, 'phone_ip', ''),
            "phone_token": getattr(self, 'phone_token', '')
        }
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {str(e)}")

    def _init_audio_stream(self):
        return self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=2048,
            input_device_index=self.selected_mic,
            stream_callback=self._audio_callback,
            start=True
        )

    def _restart_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.stream = self._init_audio_stream()

    def _find_device_index_by_name(self, device_name, input=True):
        device_count = self.p.get_device_count()
        for i in range(device_count):
            device_info = self.p.get_device_info_by_index(i)
            if input and device_info.get('maxInputChannels', 0) > 0:
                if device_name.lower() in device_info.get('name', '').lower():
                    return i
            elif not input and device_info.get('maxOutputChannels', 0) > 0:
                if device_name.lower() in device_info.get('name', '').lower():
                    return i
        return 0

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_queue.put((in_data, time.time()))
        return (in_data, pyaudio.paContinue)

    def _check_silence(self, audio_data):
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(np.square(audio_np.astype(np.float32))))
        return rms < self.silence_threshold

    def request_confirmation(self, handler):
        self.awaiting_confirmation = True
        self.confirmation_handler = handler
        self.confirmation_start_time = time.time()

    def _process_audio(self):
        while self.audio_thread._running:
            try:
                data, timestamp = self.audio_queue.get(timeout=0.5)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    recognized_text = result.get('text', '').lower()
                    print(f"Распознанный текст: {recognized_text}")
                    if recognized_text:
                        if not self.is_activated and not self.awaiting_confirmation:
                            if any(phrase in recognized_text for phrase in self.activation_phrases):
                                self.is_activated = True
                                self.state_changed.emit(True)
                                self.last_activity_time = time.time()
                                self.expecting_command = True
                                print("\nАктивирован! Говорите команду в течение 5 секунд...")
                        elif self.expecting_command:
                            self._handle_command(recognized_text)
                            self.expecting_command = False
                            if not self.awaiting_confirmation:
                                self.is_activated = False
                                self.state_changed.emit(False)
                                print("Ожидание активации...")
                        elif self.awaiting_confirmation:
                            new_state = self.confirmation_handler.handle_confirmation(recognized_text, self)
                            if new_state is None:
                                self.awaiting_confirmation = False
                                self.confirmation_handler = None
                                self.is_activated = False
                                self.state_changed.emit(False)
                            else:
                                self.awaiting_confirmation = True
                else:
                    pass
            except queue.Empty:
                if self.is_activated and (time.time() - self.last_activity_time > self.command_timeout):
                    print("\nТаймаут. Ожидание активационной фразы...")
                    self.is_activated = False
                    self.state_changed.emit(False)
                    self.expecting_command = False
                if self.awaiting_confirmation and (time.time() - self.confirmation_start_time > self.confirmation_timeout):
                    print("\nТаймаут подтверждения. Ожидание активационной фразы...")
                    self.awaiting_confirmation = None
                    self.confirmation_handler = None
                    self.state_changed.emit(False)
                continue

    def _handle_command(self, text):
        text_lower = text.lower()
        print(f"Обработка команды: {text_lower}")
        result = self.command_handler.handle(text_lower, self)
        response = result['response']
        confirmation = result.get('confirmation')
        print(response)
        if confirmation:
            self.request_confirmation(confirmation)
        if not self.awaiting_confirmation:
            self.is_activated = False
            self.state_changed.emit(False)
            print("Ожидание активации...")

    def start(self):
        print("Ожидание активационной фразы...")
        self.audio_thread._running = True
        self.audio_thread.start()

    def stop(self):
        self.audio_thread._running = False
        self.audio_thread.quit()
        self.audio_thread.wait()
        self._save_settings()
        self.is_activated = False
        self.state_changed.emit(False)
        self.stopped.emit()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("Работа ассистента остановлена")