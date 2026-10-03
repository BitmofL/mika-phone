from flask import Flask, request
import os
import playsound  # Для воспроизведения звука
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "/storage/emulated/0/Download"  # Папка для загрузки файлов на Android
ALLOWED_TOKEN = "your_phone_token_here"  # Установите свой токен

@app.route('/find', methods=['POST'])
def find_phone():
    token = request.headers.get('Authorization', '').replace("Bearer ", "")
    if token != ALLOWED_TOKEN:
        return "Unauthorized", 401
    playsound.playsound("path_to_sound.mp3")  # Укажите путь к звуковому файлу
    return "Phone is ringing", 200

@app.route('/open_app', methods=['POST'])
def open_app():
    token = request.headers.get('Authorization', '').replace("Bearer ", "")
    if token != ALLOWED_TOKEN:
        return "Unauthorized", 401
    data = request.json
    app_name = data.get("app_name")
    # Пример для Android (нужен ADB или аналогичный инструмент)
    subprocess.run(["adb", "shell", "monkey", "-p", app_name, "-c", "android.intent.category.LAUNCHER", "1"])
    return f"Opened {app_name}", 200

@app.route('/upload', methods=['POST'])
def upload_file():
    token = request.headers.get('Authorization', '').replace("Bearer ", "")
    if token != ALLOWED_TOKEN:
        return "Unauthorized", 401
    file = request.files['file']
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return "File uploaded", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)