@echo off
title Hongguo Direct FastAPI (No License Key)
cd /d "%~dp0"

echo ============================================================
echo   Hongguo Direct FastAPI Server (Bypass License Key)
echo ============================================================
echo.

set HG_LICENSE_DISABLED=1
set SIGN_SERVER=http://127.0.0.1:9099
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: Check if port 9099 is listening
netstat -ano -p TCP | findstr /R /C:":9099 *LISTENING" >nul
if errorlevel 1 (
    echo [1/2] Starting offline signer on port 9099...
    start /B "" ".\jre\bin\java.exe" -Xmx512m -XX:+ExitOnOutOfMemoryError --add-opens java.base/java.lang=ALL-UNNAMED -cp unidbg-sign.jar com.hongguo.sign.FqTrace serve 9099
    timeout /t 3 /nobreak >nul
) else (
    echo [1/2] Offline signer is already running on :9099.
)

echo [2/2] Starting FastAPI Server on http://127.0.0.1:8000 ...
echo Swagger UI Documentation: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
echo.

".\python\python.exe" direct_fastapi.py

pause
