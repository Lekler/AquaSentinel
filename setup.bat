@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo Instalacao concluida. Abra run.bat.
pause
exit /b 0
:erro
echo A instalacao falhou. Confira o Python 3.12 e a conexao.
pause
exit /b 1
