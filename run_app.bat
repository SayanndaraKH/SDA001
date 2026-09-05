@echo off
cd /d "%~dp0"
set HG_LICENSE_DISABLED=1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if exist ".\python\pythonw.exe" (
    start "" ".\python\pythonw.exe" main.py
) else (
    start "" python main.py
)
