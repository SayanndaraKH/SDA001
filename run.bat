@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SYD DOWNLOADER PRO - DESKTOP APP

set HG_LICENSE_DISABLED=1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if exist "python\pythonw.exe" (
    start "" ".\python\pythonw.exe" main.py
) else if exist "python\python.exe" (
    start "" ".\python\python.exe" main.py
) else (
    start "" python main.py
)
