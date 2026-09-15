@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo The project environment is not installed. Follow the setup in README.md.
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -I -B -m blastradius review %*