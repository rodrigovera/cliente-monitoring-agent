# 🧾 Cliente de Monitoreo – FastAPI + Docker

Este es el agente cliente que forma parte del sistema de monitoreo distribuido. El cliente expone métricas y logs para que una máquina central pueda recolectarlas y visualizarlas en Grafana.

---

## 🚀 Requisitos del sistema

- Ubuntu 22.04 LTS (recomendado)
- Acceso a internet
- Acceso por consola (SSH)

---

## 📦 Programas necesarios

### 🔹 Docker + Docker Compose

Ejecuta estos comandos para instalar Docker con Compose incluido:


curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# (Opcional) Añadir permisos sin sudo
sudo usermod -aG docker $USER
newgrp docker
Verifica:


docker --version
docker compose version
🔹 Git (para clonar el repositorio)

sudo apt install git -y
📁 Clonar el repositorio

git clone https://github.com/rodrigovera/cliente-monitoring-agent.git
cd cliente-monitoring-agent
⚙️ Instalación y despliegue
Ejecuta el instalador:


bash instalar.sh
Este script:

Te pedirá el nombre del cliente y el hostname.

Creará archivos .env, carpetas necesarias y levantará los contenedores con Docker Compose.

🌐 Puertos que deben estar abiertos en el firewall
Puerto	Uso
8000	Expone la API de métricas y logs
22	Acceso SSH (solo para ti)

✅ Verifica que funciona
Después del despliegue, abre en navegador:


http://<IP_DEL_CLIENTE>:8000/docs
Ahí verás la documentación de la API FastAPI generada automáticamente.

🧹 ¿Problemas?
Asegúrate de que Docker esté corriendo:


sudo systemctl start docker
Revisa los logs:

docker compose logs -f
📄 Licencia
Este proyecto es parte de un sistema de monitoreo personalizado para fines académicos, demostrativos o comerciales. Uso bajo permiso del autor.