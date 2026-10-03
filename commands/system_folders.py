from .command import Command
import os
from pathlib import Path

class SystemFoldersCommand(Command):
    def should_handle(self, text: str) -> bool:
        text = text.lower().strip()
        return any(keyword in text for keyword in [
            "загрузки", "документы", "фото", 
            "видео", "проводник"
        ])

    def execute(self, text: str, assistant: object) -> str:
        folders = {
            "загрузки": Path.home() / "Downloads",
            "документы": Path.home() / "Documents",
            "фото": Path.home() / "Pictures",
            "видео": Path.home() / "Videos"
           
        }

        if "проводник" in text:
            self._open_explorer()
            return "Проводник запущен"

        for folder_name, path in folders.items():
            if folder_name in text:
                if path.exists():
                    os.startfile(path)
                    return f"Открываю {folder_name}"
                return f"Папка {folder_name} не найдена"
        
        return ""

    def _open_explorer(self):
        if os.name == 'nt':
            os.system('explorer')
        else:
            os.system('nautilus')