@echo off
chcp 65001 >nul
cd /d "%~dp0"
title DnD-трекер

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  ОШИБКА: не найдено окружение .venv
    echo  Создай его командой: python -m venv .venv
    echo  затем: .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo  ОШИБКА: нет файла .env со строкой подключения к базе.
    echo.
    pause
    exit /b 1
)

echo  Запускаю DnD-трекер...
echo  Это окно не закрывай - в нём работает сервер.
echo  Остановка сервера: Ctrl+C или просто закрой окно.
echo.

start "" /min cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

".venv\Scripts\python.exe" -m uvicorn main:app --reload

echo.
echo  Сервер остановлен.
pause