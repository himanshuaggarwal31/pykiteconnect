# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
.\venv\Scripts\Activate

# Install requirements
Write-Host "Installing requirements..."
pip install -r requirements.txt

Write-Host "`nSetup complete! You can now run the application with:"
Write-Host "python run.py"
