@echo off
echo ===============================
echo   🧾 Instalador de Monitoreo
echo ===============================

set /p nombre=👉 Nombre del cliente (job):
set /p instancia=💡 Nombre de la instancia (hostname):

echo NOMBRE_CLIENTE=%nombre% > .env
echo NOMBRE_INSTANCIA=%instancia% >> .env

echo ----------------------------------
echo 🛠️ Preparando carpetas necesarias...
if not exist logs mkdir logs
if not exist positions mkdir positions

echo 🔄 Reiniciando contenedores...
docker compose down

echo 🚀 Levantando el stack con Docker...
docker compose up --build -d

echo.
echo ✅ Cliente desplegado exitosamente.
echo 🌐 Accede a http://localhost:8000/docs para verificar
pause
