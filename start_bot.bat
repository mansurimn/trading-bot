@echo off

echo =========================
echo Starting Trading Bot...
echo =========================

:: Start Python bot
start cmd /k python bot.py

timeout /t 3

echo =========================
echo Starting ngrok...
echo =========================

:: Start ngrok
start cmd /k ngrok http 5000

echo =========================
echo Both started successfully
echo =========================

pause