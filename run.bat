@echo off
setlocal
cd /d "%~dp0"
set "AQUA_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%AQUA_PY%" (
  echo Execute setup.bat primeiro.
  pause
  exit /b 1
)
"%AQUA_PY%" -m streamlit run app.py --server.headless false
if errorlevel 1 pause
