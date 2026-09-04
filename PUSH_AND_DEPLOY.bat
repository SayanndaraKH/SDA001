@echo off
chcp 65001 >nul
title SYD Downloader Pro - PUSH & DEPLOY TO RAILWAY
color 0B

echo ================================================================
echo    🚀 SYD Downloader Pro - Auto Push & Deploy to Railway
echo ================================================================
echo.

cd /d "%~dp0"

:: Check Git installation
where git >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Git មិនត្រូវបានរកឃើញនៅក្នុងប្រព័ន្ធកុំព្យូទ័រនេះទេ!
    echo សូមដំឡើង Git ជាមុនសិន។
    echo.
    pause
    exit /b 1
)

echo [*] កំពុងពិនិត្យមើលស្ថានភាពឯកសារ (Git Status)...
echo ----------------------------------------------------------------
git status -s
echo ----------------------------------------------------------------
echo.

:: Check if there are any changes
git status --porcelain | findstr /R "." >nul
if %errorlevel% neq 0 (
    echo [INFO] មិនមានឯកសារផ្លាស់ប្តូរថ្មីទេ (Working tree clean)។
    set /p FORCE_PUSH="តើអ្នកចង់ Push ម្តងទៀតដែរឬទេ? (y/n, default=n): "
    if /i not "%FORCE_PUSH%"=="y" (
        echo.
        echo [OK] បញ្ចប់ការងារ។ Railway កំពុងដំណើរការកូដចុងក្រោយបង្អស់។
        echo.
        pause
        exit /b 0
    )
)

:: Get Commit Message
set "DEFAULT_MSG=Auto update and deploy (%date% %time%)"
echo.
set /p USER_MSG="សូមបញ្ចូលសារ Commit (ចុច Enter យក: %DEFAULT_MSG%): "
if "%USER_MSG%"=="" set "USER_MSG=%DEFAULT_MSG%"

echo.
echo [*] កំពុងរៀបចំឯកសារ (git add -A)...
git add -A

echo [*] កំពុងធ្វើការ Commit: "%USER_MSG%"...
git commit -m "%USER_MSG%" >nul 2>nul
if %errorlevel% neq 0 (
    echo (គ្មានអ្វីថ្មីត្រូវ Commit បន្តដំណើរការ Push...)
)

echo.
echo [*] កំពុង Push ឡើងទៅ GitHub (origin main)...
echo ----------------------------------------------------------------
git push origin main
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ================================================================
    echo ❌ [ERROR] ការ Push ឡើង GitHub បរាជ័យ!
    echo សូមពិនិត្យមើលការភ្ជាប់អ៊ីនធឺណិត ឬសិទ្ធិ Git របស់អ្នក។
    echo ================================================================
    echo.
    pause
    exit /b 1
)

color 0A
echo.
echo ================================================================
echo ✅ ជោគជ័យ ១០០%! (PUSH COMPLETED SUCCESSFULLY)
echo ================================================================
echo.
echo 📡 កូដត្រូវបានបញ្ជូនទៅកាន់ GitHub: https://github.com/SayanndaraKH/SDA001
echo 🔄 Railway កំពុងចាប់ផ្តើម Build & Deploy ដោយស្វ័យប្រវត្តិ!
echo.
echo 🔗 ចូលមើលស្ថានភាព Deploy:
echo    https://railway.com/project/936cc339-8e6b-4b0a-a989-f04c6b6777c7
echo.
echo ================================================================
echo.
pause
