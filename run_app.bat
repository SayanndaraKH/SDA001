@echo off
cd /d "%~dp0"
set HG_LICENSE_DISABLED=1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
start "" ".\python\pythonw.exe" app.py
