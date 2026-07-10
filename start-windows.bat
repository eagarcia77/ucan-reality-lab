@echo off
setlocal
if not exist .env copy .env.example .env >nul
docker compose up --build -d
start http://localhost:8151
echo UCAN Reality Lab iniciado en http://localhost:8151
pause
