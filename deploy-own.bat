@echo off
title EdgeStore - Custom Deployment Launcher
echo ============================================================
echo   Launching EdgeStore Custom Appliance Deployment...
echo ============================================================
powershell -ExecutionPolicy Bypass -File "%~dp0deploy-own.ps1"
pause
