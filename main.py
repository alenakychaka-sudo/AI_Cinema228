from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
class Message(BaseModel):
    question: str
    answer: str
class BotRequest(BaseModel):
    user_id: int
    consversion: list[Message]

app = FastAPI()
app = FastAPI()

@app.get("/ping")

async def ping_server():
    return {"status": "Kinotavr is alive!"}

@app.post('/chat')
async def process_chat(request: BotRequest):
    histori_lenght = len(request.consversion)
    return {
        "status": "success",
        "message": f"Юзер {request.user_id} прислал {histori_lenght} сообщений"
    }
