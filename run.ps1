Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Write-Host "Installing dependencies..." -ForegroundColor Cyan
# pip install -r requirements.txt

Write-Host "Starting Flask app..." -ForegroundColor Green
$env:FLASK_APP = "app.py"
flask run --host=0.0.0.0 --port=5000

Read-Host "Press Enter to exit"
