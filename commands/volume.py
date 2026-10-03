from commands.command import Command
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math
import re

class VolumeCommand(Command):
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
        
    def should_handle(self, text: str) -> bool:
        text = self._normalize(text)
        return any(word in text for word in [
            "громк", "звук", "тише", "громче", 
            "выключи", "включи", "уровен", "процент","половина","полная","максимум","средняя" , "минимальная", "0%", "минимум"
        ])

    def execute(self, text: str, assistant: object) -> dict:
        text = self._normalize(text)
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        
        # Извлечение числового значения
        percent = self._extract_percent(text)
        
        # Обработка различных формулировок
        if self._match(text, ["выключи звук", "отключи звук", "без звука"]):
            self.volume.SetMute(1, None)
            return {'response': "Звук выключен", 'confirmation': None}
            
        elif self._match(text, ["включи звук", "верни звук"]):
            self.volume.SetMute(0, None)
            return {'response': "Звук включен", 'confirmation': None}
            
        elif percent is not None:
            volume_level = percent / 100.0
            self.volume.SetMasterVolumeLevelScalar(volume_level, None)
            return {'response': f"Громкость {percent}%", 'confirmation': None}
            
        elif self._match(text, ["полная", "максимум", "на всю" , "максимальная"]):
            self.volume.SetMasterVolumeLevelScalar(1.0, None)
            return {'response': "Громкость 100%", 'confirmation': None}
            
        elif self._match(text, ["половина", "среднюю", "50%","половину",]):
            self.volume.SetMasterVolumeLevelScalar(0.5, None)
            return {'response': "Громкость 50%", 'confirmation': None}
        
        elif self._match(text, ["минимальная", "0%", "минимум"]):
            self.volume.SetMasterVolumeLevelScalar(0.0, None)
            return {'response': "Громкость 0%", 'confirmation': None}

        elif self._match(text, ["громче", "прибавь", "+"]):
            new_vol = min(1.0, current_volume + 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_vol, None)
            return {'response': f"Громкость {math.ceil(new_vol*100)}%", 'confirmation': None}
            
        elif self._match(text, ["тише", "убавь", "-"]):
            new_vol = max(0.0, current_volume - 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_vol, None)
            return {'response': f"Громкость {math.ceil(new_vol*100)}%", 'confirmation': None}
            
        return {'response': "Не понял команду управления звуком", 'confirmation': None}

    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Удаляем пунктуацию
        return text

    def _match(self, text: str, keywords: list) -> bool:
        return any(keyword in text for keyword in keywords)

    def _extract_percent(self, text: str):
        # Поиск чисел от 0 до 100 с возможными указаниями процентов
        match = re.search(r'(?:\b|\s)(\d{1,3})\s?(?:процентов|проц|%|proc)?\b', text)
        if match:
            value = int(match.group(1))
            return max(0, min(100, value))
        return None