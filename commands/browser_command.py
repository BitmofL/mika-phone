from commands.command import Command
import webbrowser
import re

class BrowserCommand(Command):
    def _normalize_text(self, text):
        return text.lower().strip()

    def should_handle(self, text: str) -> bool:
        text = self._normalize_text(text)
        return any(keyword in text for keyword in [
            "браузер", "открой", "поиск", "ютуб", "почту", "вконтакте", "вк", "включи", "видео", "хочу посмотреть"
        ])

    def execute(self, text: str, assistant: object) -> dict:  # Изменяем тип возвращаемого значения на dict
        text = self._normalize_text(text)

        # Открытие только браузера без указания страницы
        if "браузер" in text and any(keyword in text for keyword in ["открой", "включи", "хочу посмотреть"]):
            if not any(site in text for site in ["поиск", "ютуб", "почту", "вконтакте", "вк", "видео"]):
                try:
                    webbrowser.open_new("opera.exe")  # Открывает браузер по умолчанию без URL
                    return {'response': "Браузер открыт", 'confirmation': None}
                except webbrowser.Error as e:
                    return {'response': f"Ошибка при открытии браузера: {str(e)}", 'confirmation': None}

        # Открытие определенных сайтов
        sites = {
            "ютуб": "https://www.youtube.com",
            "видео": "https://www.youtube.com",
            "почту": "https://mail.google.com",
            "вконтакте": "https://vk.com"
        }
        
        for site_name, url in sites.items():
            if site_name in text:
                try:
                    webbrowser.open(url)
                    return {'response': f"Открываю {site_name}", 'confirmation': None}
                except webbrowser.Error as e:
                    return {'response': f"Ошибка при открытии {site_name}: {str(e)}", 'confirmation': None}

        # Поисковый запрос
        if "поиск" in text:
            match = re.search(r"поиск\s+(.+)", text)
            if match:
                query = match.group(1).replace(" ", "+")
                search_url = f"https://yandex.ru/search/?text={query}"
                try:
                    webbrowser.open(search_url)
                    return {'response': f"Выполняю поиск: {match.group(1)}", 'confirmation': None}
                except webbrowser.Error as e:
                    return {'response': f"Ошибка при выполнении поиска: {str(e)}", 'confirmation': None}
        
        return {'response': "Не понял команду для браузера", 'confirmation': None}