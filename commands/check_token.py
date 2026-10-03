import commands.control_kojima_bulb as bulb_control

new_access_token, new_refresh_token = bulb_control.get_new_tokens()
if new_access_token:
    print(f"Новый access_token: {new_access_token}")
    print(f"Новый refresh_token: {new_refresh_token}")
else:
    print("Не удалось обновить токены")