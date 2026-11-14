@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
  echo [ISHARA] Primary UI failed. Starting the Tkinter fallback...
  ".venv\Scripts\python.exe" main.py --fallback
)

