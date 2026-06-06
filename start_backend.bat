@echo off
echo Starting FastAPI backend...
cd /d D:\AI_Cinema228
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 7777 --reload
