import requests

# Конфигурация
CLIENT_ID = "1675d8116ebc4ff1b308019f8b774f0b"
CLIENT_SECRET = "d0015496da674bc28915e0d8cee9d3c9"
REDIRECT_URI = "https://oauth.yandex.ru/verification_code"
DEVICE_ID = "be091e5e-24f4-449a-9f25-bd0eadb28e49"
ACCESS_TOKEN = "y0__xCCmt6NBBjsxTcgqI-ogxMG10diEa9UPauwIehk244EnBgtRA"
REFRESH_TOKEN = "1:AAA:1:dz5PQwSjqPvKl7AB:_SgXS87DuhNqzp28K_4aZ-t2DHO1UzhYSk2jkjzI9vUwso30aklwD0kBe_n2f5Oa3YX2LaI:XLJgVwPPuuO5DNXq2H5XZA"
AUTH_URL = "https://oauth.yandex.ru/token"
API_URL = "https://api.iot.yandex.net/v1.0"

def get_new_tokens():
    """Получение нового access_token через refresh_token"""
    try:
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        response = requests.post(AUTH_URL, data=auth_data)
        response.raise_for_status()
        tokens = response.json()
        return tokens.get("access_token"), tokens.get("refresh_token")
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e.response.status_code}")
        print("Ответ сервера:", e.response.text)
        return None, None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None

def send_action(access_token: str, action_type: str, instance: str, value):
    """Отправка действия на устройство"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_URL}/devices/{DEVICE_ID}/actions"
    payload = {
        "actions": [{
            "type": action_type,
            "state": {"instance": instance, "value": value}
        }]
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Команда выполнена: {action_type} - {instance}: {value}")
        print(f"Ответ API: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e.response.status_code}")
        print("Ответ сервера:", e.response.text)
        return None
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def get_device_state(access_token: str, device_id: str):
    """Получить текущее состояние устройства"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_URL}/devices/{device_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        device_info = response.json()
        return device_info.get("capabilities", [])
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e.response.status_code}")
        print("Ответ сервера:", e.response.text)
        return None
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def restore_device_state(access_token: str, device_id: str, capabilities):
    """Восстановить состояние устройства"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_URL}/devices/{device_id}/actions"
    payload = {
        "actions": capabilities
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("Состояние устройства восстановлено")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e.response.status_code}")
        print("Ответ сервера:", e.response.text)
        return None
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def turn_on(access_token: str):
    """Включить лампочку"""
    return send_action(access_token, "devices.capabilities.on_off", "on", True)

def turn_off(access_token: str):
    """Выключить лампочку"""
    return send_action(access_token, "devices.capabilities.on_off", "on", False)

def set_brightness(access_token: str, brightness: int):
    """Установить яркость (1-100)"""
    if 1 <= brightness <= 100:
        return send_action(access_token, "devices.capabilities.range", "brightness", brightness)
    else:
        print("Яркость должна быть от 1 до 100")
        return None

def set_temperature(access_token: str, temperature_k: int):
    """Установить температуру цвета (2700-6500 K)"""
    if 2700 <= temperature_k <= 6500:
        return send_action(access_token, "devices.capabilities.color_setting", "temperature_k", temperature_k)
    else:
        print("Температура цвета должна быть от 2700 до 6500 K")
        return None

def set_color_scene(access_token: str, scene_id: str):
    """Установить цветовую сцену"""
    available_scenes = [
        "alice", "candle", "fantasy", "garland", "jungle", "neon", "night",
        "ocean", "party", "reading", "rest", "romance", "new_year", "halloween", "breathing"
    ]
    if scene_id in available_scenes:
        return send_action(access_token, "devices.capabilities.color_setting", "scene", scene_id)
    else:
        print(f"Недоступная сцена: {scene_id}. Доступные сцены: {', '.join(available_scenes)}")
        return None

def set_color(access_token: str, rgb: tuple):
    """Установить цвет в формате RGB"""
    try:
        r, g, b = rgb
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            print("Значения RGB должны быть от 0 до 255")
            return None
        color_value = (r << 16) + (g << 8) + b
        print(f"Установка RGB цвета: ({r}, {g}, {b}) -> {color_value}")
        return send_action(access_token, "devices.capabilities.color_setting", "rgb", color_value)
    except ValueError:
        print("RGB должен быть кортежем из трех чисел (r, g, b)")
        return None

def set_hsv_color(access_token: str, hsv: dict):
    """Установить цвет в формате HSV"""
    try:
        h, s, v = hsv["h"], hsv["s"], hsv["v"]
        if not (0 <= h <= 360 and 0 <= s <= 100 and 0 <= v <= 100):
            print("HSV значения должны быть: h (0-360), s (0-100), v (0-100)")
            return None
        hsv_value = {"h": h, "s": s, "v": v}
        print(f"Установка HSV цвета: h={h}, s={s}, v={v}")
        return send_action(access_token, "devices.capabilities.color_setting", "hsv", hsv_value)
    except (KeyError, ValueError):
        print("HSV должен быть словарем с ключами 'h', 's', 'v'")
        return None

if __name__ == "__main__":
    access_token = ACCESS_TOKEN
    turn_on(access_token)
    set_brightness(access_token, 50)
    set_hsv_color(access_token, {"h": 0, "s": 100, "v": 100})