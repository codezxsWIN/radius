@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo The optional repository analyzer is not installed. Opening the offline lesson.
  echo Analyzer setup: Python 3.12 or newer, then python -m venv .venv
  echo and .venv\Scripts\python.exe -m pip install .
  echo Offline lesson: "%~dp0ui\index.html"
  if "%~1"=="--no-open" exit /b 0
  start "" "%~dp0ui\index.html"
  exit /b 0
)
"%~dp0.venv\Scripts\python.exe" -I -c "import sys; assert sys.version_info >= (3,12); import yaml,jsonschema,blastradius" >nul 2>nul
if errorlevel 1 (
  echo The existing environment is incomplete. It has not been modified.
  echo See README.md for repair instructions. Opening the offline lesson.
  start "" "%~dp0ui\index.html"
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -I -B -m blastradius review %*