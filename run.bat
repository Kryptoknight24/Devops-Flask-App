@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

@REM echo Installing dependencies...
@REM pip install -r requirements.txt

echo Starting Flask app...
set FLASK_APP=app.py
start "" /b flask run --host=0.0.0.0 --port=5000

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo Opening browser...
start "" http://127.0.0.1:5000

echo Flask is running. Press Ctrl+C to stop.
pause >nul
