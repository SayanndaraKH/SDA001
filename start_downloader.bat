@echo off
title SYD DOWNLOADER PRO
cd /d "%~dp0"
set HG_LICENSE_DISABLED=1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set SIGN_SERVER=http://127.0.0.1:9099
if exist ".\python\pythonw.exe" (
    start "" ".\python\pythonw.exe" main.py
) else (
    start "" python main.py
)
exit
