@echo off
echo ========================================
echo  Sovereign Quant Super Agent Dashboard
echo ========================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python from https://www.python.org/downloads/
    echo Make sure to tick "Add python.exe to PATH"
    pause
    exit /b 1
)

echo Installing / updating dependencies...
python -m pip install -r requirements.txt --quiet

echo.
echo Starting dashboard...
echo Open your browser to: http://localhost:8501
echo Press Ctrl+C to stop.
echo.

python -m streamlit run app.py --server.headless true

pause
