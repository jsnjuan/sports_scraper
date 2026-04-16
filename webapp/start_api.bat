@echo off
cd /d "%~dp0"
C:\Users\jaime\Documents\Projects\sports_scraper\venv\Scripts\python.exe -m uvicorn api.index:app --port 5328 --reload
