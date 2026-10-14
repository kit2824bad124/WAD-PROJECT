@echo off
title Student Skill & Placement Tracker
echo ================================================================
echo    Student Skill ^& Placement Tracker - Web Application
echo ================================================================
echo.

IF EXIST venv\Scripts\python.exe (
    echo [*] Starting application using local virtual environment...
    venv\Scripts\python.exe app.py
) ELSE (
    echo [*] Starting application using system Python...
    python app.py
)

pause
