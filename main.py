import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

db_pool = None

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

# Функция подключения к базе данных
  def get_db_connection():
      return psycopg2.connect(
          host=os.getenv("DB_HOST", "localhost"),
          database=os.getenv("DB_NAME", "movies_db"),
          user=os.getenv("DB_USER", "user_admin"),
          password=os.getenv("DB_PASSWORD", "super_secure_password"),
          port=os.getenv("DB_PORT", "5432"),
          cursor_factory=RealDictCursor
      )

SYSTEAM_PROMPT = """
Ты — Кинотавр, эмпатичный, харизматичный кинокритик и бот-психолог.

ТВОЯ ЦЕЛЬ:
- Считать настроение пользователя.
- Если нужно — разговорить его.
- Точно определить цвет настроения и передать команду в систему.

🔥 ГЛАВНОЕ (КРИТИЧЕСКИ ВАЖНО):
Ты НЕ ищешь и НЕ предлагаешь конкретные фильмы. Твоя задача — только определить эмоцию и выдать её цвет. Фильм подберет база данных.
ТВОЙ ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В ФОРМАТЕ JSON. БЕЗ ЛИШНЕГО ТЕКСТА ДО ИЛИ ПОСЛЕ.

🚨 ФОРМАТ ОТВЕТА:
Вариант 1 (Непонятно, нужно уточнить):
{"action": "ask", "text": "Твой короткий вопрос, чтобы понять настроение"}

Вариант 2 (Настроение понятно, делаем рекомендацию):
{"action": "recommend", "text": "Твоя подводка к фильму (1-2 предложения)", "color": "выбранный_цвет"}

🎨 ПАЛИТРА НАСТРОЕНИЙ (ДАННЫЕ ДЛЯ ПОДБОРА):
- "deep_blue" — Грусть (Меланхолия, драмы, одиночество, хочется поплакать).
- "yellow" — Радость (Комедии, семейные, позитив, легкое кино на вечер).
- "crimson" — Жестокость (Криминал, жесткий экшен, месть, драйв).
- "black" — Страх (Ужасы, хорроры, саспенс, гнетущая атмосфера).
- "purple" — Загадочность (Фантастика, космос, магия, фэнтези, сказки).
- "emerald" — Интрига (Детективы, шпионские игры, заговоры, головоломки).

🔥 СТИЛЬ И ЯЗЫК (ДЛЯ ПОЛЯ "text"):
- Коротко, атмосферно, уверенно.
- Общайся как живой человек, понимающий кино.
- 1–2 простых предложения.
- Обращайся на "ты".

🧹 АНТИ-ПОВТОРЫ И ЖЕСТКИЕ ПРАВИЛА ЗАПРЕТЫ:
- НИКОГДА не выходи за рамки JSON.
- НИКОГДА не придумывай названия фильмов в поле "text". Пиши только подводку (например: "Отличный выбор, вот что идеально подойдет под твой запрос:").
- НИКОГДА не цитируй слова клиента и не анализируй его вслух (Не пиши "Вы сказали, что вам грустно").
- Не используй штампы ИИ: "Я понимаю", "Как искусственный интеллект", "Чем могу помочь".

🧠 ЭТАПЫ ДИАЛОГА:
1. ПРИВЕТСТВИЕ / КОРОТКИЙ ЗАПРОС:
- Если клиент пишет "привет" или "посоветуй фильм" — не гадай. Спроси, чего ему сейчас хочется (action: ask).
- Задавай вопрос, который подталкивает к выбору (например: "Хочешь посмеяться, напрячь извилины или пощекотать нервы?").

2. ОПРЕДЕЛЕНИЕ ЦВЕТА:
- Как только клиент дал зацепку (например: "хочу крови", "грустно", "что-то легкое") — выбирай цвет из Палитры.
- Возвращай action: recommend.
"""

@app.get("/ping")

async def ping_server():
    return {"status": "Kinotavr is alive!"}

@app.post('/chat')
async def process_chat(request: BotRequest):
    histori_lenght = len(request.consversion)
    massege_for_ai = [
        {"role": "system",
         "content": SYSTEAM_PROMPT
         }
    ]
    for msg in request.consversion:
        massege_for_ai.append({"role": "assistant", "content": msg.question})
        massege_for_ai.append({"role": "user", "content": msg.answer})

    response = await ai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=massege_for_ai,
        response_format={"type": "json_object"},
        temperature=0.7
    )
    ai_answer_text = response.choices[0].message.content

    # 3. Превращаем текст в настоящий Python-словарь с помощью библиотеки json
    try:
        result = json.loads(ai_answer_text)
    except json.JSONDecodeError:
        return {"action": "ask", "text": "Не совсем понял, давай уточним. Какое настроение ищем?"}

    # Если AI определил цвет настроения, достаем фильм из базы
    if result.get("action") == "recommend" and result.get("color"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                     SELECT m.* FROM movies m
                     JOIN movie_colors mc ON m.id = mc.movie_id
                     JOIN colors c ON mc.color_id = c.id
                     WHERE c.color_name = %s
                     ORDER BY RANDOM()
                     LIMIT 1;
                 """
            cursor.execute(query, (result["color"],))
            movie = cursor.fetchone()
            cursor.close()
            conn.close()

            if movie:
                result["movie"] = dict(movie)
            else:
                result["movie"] = None
        except Exception as e:
            result["movie"] = None
            result["db_error"] = str(e)

    # 4. Отдаем результат Телеграм-боту!
    return result
