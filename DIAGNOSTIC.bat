@echo off
cd /d "%~dp0"
echo TubeForge diagnostic mode
echo.
py -3 --version
echo.
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
echo.
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
.venv\Scripts\python.exe app.py
pause
