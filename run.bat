@echo off
setlocal
cd /d %~dp0

if not exist .venv (
  py -m venv .venv
)

set PYTHON_EXE=%CD%\.venv\Scripts\python.exe
%PYTHON_EXE% -m pip install --upgrade pip >nul
%PYTHON_EXE% -m pip install -e . >nul
%PYTHON_EXE% app.py %*
exit /b %ERRORLEVEL%
