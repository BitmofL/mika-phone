from abc import ABC, abstractmethod
import re

class Command(ABC):
    @abstractmethod
    def should_handle(self, text: str) -> bool:
        pass
    
    @abstractmethod
    def execute(self, text: str, assistant: object) -> str:
        pass

    def _normalize_text(self, text: str) -> str:
        # Приводим текст к нижнему регистру и удаляем лишние символы
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def _contains_any(self, text: str, keywords: list) -> bool:
        # Проверяем наличие хотя бы одного ключевого слова
        return any(keyword in text for keyword in keywords)
    
class Command:
    def should_handle(self, text):
        raise NotImplementedError()

    def execute(self, text, assistant):
        raise NotImplementedError()