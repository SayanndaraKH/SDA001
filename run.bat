@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SYD DOWNLOADER PRO - WEBSITE MODE

if exist "python\python.exe" (
    ".\python\python.exe" run_website.py
) else (
    python run_website.py
)

if errorlevel 1 (
    echo.
    pause
)
