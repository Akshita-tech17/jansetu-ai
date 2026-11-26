@echo off
cd /d "%~dp0"
echo ========================================================
echo   Starting JanSetu AI Prototype (AI Kaushal Hackathon)
echo ========================================================
echo.
echo Current Directory: %CD%
echo Local URL: http://localhost:8000
echo Opening JanSetu AI Split-Screen in browser...
start http://localhost:8000
"C:\Users\acer\AppData\Local\Programs\Python\Python314\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
