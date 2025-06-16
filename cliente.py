from fastapi import FastAPI, Request
import psutil
import logging
from datetime import datetime
import threading
import time
import requests
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import delete_from_gateway
import os


log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=f"{log_dir}/errors.json",
    level=logging.ERROR,
    format='{"timestamp": "%(asctime)s", "error": "%(message)s"}'
)

# 🔹 Ingreso interactivo de nombre e instancia
NOMBRE = input("🧾 Ingrese el nombre del cliente (job): ").strip()
INSTANCE = input("💡 Ingrese el nombre de la instancia (hostname): ").strip()
PUSHGATEWAY_URL = "http://20.55.80.149:9091"

app = FastAPI()

# Contador global para middleware
http_requests_total_counter = Counter(
    "http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "endpoint", "instance"]
)

@app.middleware("http")
async def contar_http_requests(request: Request, call_next):
    response = await call_next(request)
    http_requests_total_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        instance=INSTANCE
    ).inc()
    return response

# Configuración de logs JSON
logging.basicConfig(
    filename="/app/logs/errors.json",
    level=logging.ERROR,
    format='{"timestamp": "%(asctime)s", "error": "%(message)s"}'
)

@app.get("/metrics")
def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

@app.get("/metrics_prometheus")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/causar_error")
def causar_error():
    try:
        raise ValueError("Esto es un error simulado desde el CLIENTE")
    except Exception as e:
        logging.error(str(e))
        raise

def push_metrics():
    registry = CollectorRegistry()

    cpu_gauge = Gauge("cpu_percent", "CPU usage (%)", ["instance"], registry=registry)
    mem_gauge = Gauge("memory_percent", "RAM usage (%)", ["instance"], registry=registry)
    disk_gauge = Gauge("disk_usage", "Disk usage (%)", ["instance"], registry=registry)

    registry.register(http_requests_total_counter)

    # Inicializa etiquetas
    http_requests_total_counter.labels(
        method="INIT",
        endpoint="/",
        instance=INSTANCE
    ).inc(0)

    while True:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent

            cpu_gauge.labels(instance=INSTANCE).set(cpu)
            mem_gauge.labels(instance=INSTANCE).set(mem)
            disk_gauge.labels(instance=INSTANCE).set(disk)
            delete_from_gateway(
                gateway=PUSHGATEWAY_URL.replace("http://", ""),
                job=NOMBRE,
                grouping_key={"instance": INSTANCE}
            )

            push_to_gateway(
                PUSHGATEWAY_URL.replace("http://", ""),
                job=NOMBRE,
                registry=registry,
		
            )

            print(f"[Push] ✅ Métricas empujadas desde '{NOMBRE}' ({INSTANCE})")
        except Exception as e:
            print(f"[Push] ❌ Error al enviar métricas: {e}")
        time.sleep(15)

# 🔹 Activar hilo para push automático
threading.Thread(target=push_metrics, daemon=True).start()
