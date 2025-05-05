import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

# Указываем имя сессии и метаданные устройства
client = TelegramClient(
    'session', api_id, api_hash,
    device_model='GardenBot-Server',
    system_version='Ubuntu-22.04'
)


async def main():
    # Запускаем первый раз, чтобы сохранить session.session
    await client.start()  
    print(f"✔️ Telethon авторизован как {await client.get_me()}")

if __name__ == '__main__':
    client.loop.run_until_complete(main())
