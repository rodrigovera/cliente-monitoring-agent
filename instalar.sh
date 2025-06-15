#!/bin/bash

echo "🧾 Instalador de cliente de monitoreo"
read -p "👉 Nombre del cliente (job): " cliente
read -p "💡 Nombre de la instancia (hostname): " instancia

echo "NOMBRE_CLIENTE=$cliente" > .env
echo "NOMBRE_INSTANCIA=$instancia" >> .env

echo "🛠️ Construyendo contenedores..."
mkdir -p logs positions
docker compose down
docker compose up -d --build

echo "✅ Cliente desplegado exitosamente."
echo "🌐 Visita http://localhost:8000/docs para probar la API"
