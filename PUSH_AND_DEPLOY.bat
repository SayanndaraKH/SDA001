@echo off
setlocal
cd /d "%~dp0"
title SYD Downloader Pro - PUSH AND DEPLOY

if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" push_deploy.py
) else (
    python push_deploy.py
)

if errorlevel 1 (
    echo.
    echo An unexpected error occurred.
    pause
)
