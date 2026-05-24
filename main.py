import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json
from openai import OpenAI, AsyncOpenAI


class Message(BaseModel):
    question: str
    answer: str
class BotRequest(BaseModel):
    user_id: int
    consversion: list[Message]

app = FastAPI()

ai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
@app.get("/ping")

async def ping_server():
    return {"status": "Kinotavr is alive!"}

@app.post('/chat')
async def process_chat(request: BotRequest):
    histori_lenght = len(request.consversion)
    massege_for_ai = [
        {"role": "system", "content": "Ты бот Кинотавр. Узнай настроение пользователя и порекомендуй фильм."}
    ]
    for msg in request.consversion:
        massege_for_ai.append({"role": "assistant", "content": msg.question})
        massege_for_ai.append({"role": "user", "content": msg.answer})
    return {"result": massege_for_ai}
