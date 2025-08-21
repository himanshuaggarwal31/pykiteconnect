# Go to project folder
Set-Location "C:\Himanshu\REPOS\mygttapp\pykiteconnect"

# Activate virtual environment
& "C:\Himanshu\REPOS\mygttapp\pykiteconnect\venv\Scripts\Activate.ps1"

# Run AutoConnect.py (step 1)
python .\app\AutoConnect.py

# After it finishes, run run.py (step 2)
python .\gtt_webapp\run.py
