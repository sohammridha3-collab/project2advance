@echo off
title Heart Risk Prediction API Backend
cd /d "%~dp0"
echo ========================================================
echo  Starting Heart Risk Prediction API Backend
echo  API Docs:  http://127.0.0.1:8000/docs
echo  Health:    http://127.0.0.1:8000/health
echo  App Home:  http://127.0.0.1:8000/
echo ========================================================
echo  [IMPORTANT] Keep this terminal window open while using the web app!
echo ========================================================
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause

