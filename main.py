import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

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
        {"role": "system",
         "content": "Ты бот Кинотавр. Узнай настроение пользователя и порекомендуй фильм. ОТВЕЧАЙ СТРОГО В ФОРМАТЕ JSON: {\"action\": \"ask\" или \"recommend\", \"text\": \"твой ответ\"}"
         }
    ]
    response = await ai_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=massege_for_ai,
        response_format={"type": "json_object"},
        temperature=0.7
    )
    for msg in request.consversion:
        massege_for_ai.append({"role": "assistant", "content": msg.question})
        massege_for_ai.append({"role": "user", "content": msg.answer})
    return {"result": massege_for_ai}
