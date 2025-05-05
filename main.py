import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.errors import RPCError, TimeoutError as TelethonTimeoutError
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 1) Конфиг
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
GROK_CHAT = os.getenv("GROK_CHAT")  # должно быть вида "@GrokAI"

# 2) Telethon-клиент и сессия
SESSION = os.path.join(os.path.dirname(__file__), "session")
client = TelegramClient(
    SESSION, 
    api_id, 
    api_hash,
    device_model='GardenBot-Server',  # Уникальное имя устройства
    system_version='Ubuntu-22.04'     # Уникальная версия ОС
)

# Здесь будем хранить full entity
chat_entity = None

# 3) FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(req: AskRequest):
    # 1) убедиться в подключении
    if not client.is_connected():
        await client.connect()

    try:
        # открываем «разговор» с Grok
        async with client.conversation(chat_entity, timeout=30) as conv:
            await conv.send_message(req.question)
            reply = await conv.get_response()

    except TelethonTimeoutError:
        raise HTTPException(504, "Превышено время ожидания ответа от Grok")
    except RPCError as e:
        raise HTTPException(500, f"Ошибка Telethon RPC: {e}")

    return {"answer": reply.text}

@app.get("/test")
async def test():
    if not client.is_connected():
        await client.connect()
    try:
        msg = await client.send_message(chat_entity, "Тестовое сообщение от FastAPI")
        return {"status": "ok", "message_id": msg.id}
    except RPCError as e:
        raise HTTPException(500, f"Ошибка при тестовой отправке: {e}")

@app.on_event("startup")
async def startup_event():
    # login.py уже запускали, поэтому здесь просто стартуем
    try:
        await client.start()
    except Exception as e:
        raise RuntimeError(
            "❌ Не удалось инициализировать Telethon-сессию. "
            "Сначала запустите login.py и убедитесь, что рядом лежит session.session"
        ) from e

    # Разрешаем юзернейм один раз и сохраняем entity
    global chat_entity
    chat_entity = await client.get_entity(GROK_CHAT)
    print(f"✔️ Telethon запущен, entity: {chat_entity!r}")

    # Запускаем фоновый таск, который удерживает соединение живым
    asyncio.create_task(client.run_until_disconnected())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
