@echo off
title EdgeStore Launcher
echo ===================================================
echo             Starting EdgeStore Stack...
echo ===================================================
echo.

docker compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker is not running. Please open Docker Desktop and try again.
    pause
    exit /b %errorlevel%
)

echo.
echo ===================================================
echo             EdgeStore is Live!
echo ===================================================
echo.
echo   URL:      http://localhost:8000
echo   User:     admin
echo   Pass:     AdminEdgeStore2026!
echo.
echo ===================================================
pause
