from fastapi import FastAPI
app = FastAPI()

@app.get("/ping")

async def ping_server():
    return {"status": "Kinotavr is alive!"}
