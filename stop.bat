@echo off
title EdgeStore Stopper
echo ===================================================
echo             Stopping EdgeStore Stack...
echo ===================================================
echo.

docker compose down

echo.
echo ===================================================
echo             EdgeStore Stopped Successfully!
echo ===================================================
echo.
pause
