#!/bin/bash

echo "🧾 Instalador de cliente de monitoreo"
read -p "👉 Nombre del cliente (job): " cliente
read -p "💡 Nombre de la instancia (hostname): " instancia

# 🔹 Guarda en .env para el contenedor
echo "NOMBRE_CLIENTE=$cliente" > .env
echo "NOMBRE_INSTANCIA=$instancia" >> .env

# 🔹 Exporta para que Docker Compose lo use como hostname
export NOMBRE_CLIENTE=$cliente
export NOMBRE_INSTANCIA=$instancia

echo "🛠️ Construyendo contenedores..."
mkdir -p logs positions

# 🔧 Renderiza el archivo promtail-config.yml usando Dockerize
docker compose run --rm dockerize

# 🚀 Levanta los servicios
docker compose down
docker compose up -d --build

echo "✅ Cliente desplegado exitosamente."
echo "🌐 Visita http://localhost:8000/docs para probar la API"
