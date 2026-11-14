@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo [ISHARA] Python launcher was not found. Install 64-bit Python 3.11 or 3.12.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [ISHARA] Creating Python 3.12 virtual environment...
  py -3.12 -m venv .venv
  if errorlevel 1 py -3.11 -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo [ISHARA] Could not create the virtual environment.
  pause
  exit /b 1
)

echo [ISHARA] Installing compatible dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ISHARA] Installation failed. Check the internet connection and Python version.
  pause
  exit /b 1
)

echo [ISHARA] Verifying the bundled ONNX model...
".venv\Scripts\python.exe" -c "from ai.pretrained_sign_recognizer import PretrainedSignRecognizer; from config import MODEL_DIR; r=PretrainedSignRecognizer(MODEL_DIR); print(r.status); raise SystemExit(0 if r.available else 1)"
if errorlevel 1 (
  echo [ISHARA] The model files are missing or invalid.
  pause
  exit /b 1
)

echo [ISHARA] Setup completed successfully.
pause

