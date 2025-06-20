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
import signal
import sys

# 📁 Logs en JSON
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=f"{log_dir}/errors.json",
    level=logging.ERROR,
    format='{"timestamp": "%(asctime)s", "error": "%(message)s"}'
)

# 🔐 Variables de entorno
NOMBRE = os.getenv("NOMBRE_CLIENTE", "cliente")  # job
INSTANCE = os.getenv("NOMBRE_INSTANCIA", os.getenv("HOSTNAME", "instancia"))
PUSHGATEWAY_URL = "http://20.55.80.149:9091"

# 🚀 FastAPI app
app = FastAPI()

# 📊 Contador global HTTP requests
http_requests_total_counter = Counter(
    "http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "endpoint", "job", "instance"]
)

@app.middleware("http")
async def contar_http_requests(request: Request, call_next):
    response = await call_next(request)
    http_requests_total_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        job=NOMBRE,
        instance=INSTANCE
    ).inc()
    return response

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

    cpu_gauge = Gauge("cpu_percent", "CPU usage (%)", ["job", "instance"], registry=registry)
    mem_gauge = Gauge("memory_percent", "RAM usage (%)", ["job", "instance"], registry=registry)
    disk_gauge = Gauge("disk_usage", "Disk usage (%)", ["job", "instance"], registry=registry)

    registry.register(http_requests_total_counter)

    # Inicializa etiquetas (sin sumar)
    http_requests_total_counter.labels(
        method="INIT",
        endpoint="/",
        job=NOMBRE,
        instance=INSTANCE
    ).inc(0)

    while True:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent

            cpu_gauge.labels(job=NOMBRE, instance=INSTANCE).set(cpu)
            mem_gauge.labels(job=NOMBRE, instance=INSTANCE).set(mem)
            disk_gauge.labels(job=NOMBRE, instance=INSTANCE).set(disk)

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

def limpiar_pushgateway():
    try:
        delete_from_gateway(
            gateway=PUSHGATEWAY_URL.replace("http://", ""),
            job=NOMBRE,
            grouping_key={"instance": INSTANCE}
        )
        print(f"[Exit] 🧹 Instancia '{INSTANCE}' borrada del PushGateway")
    except Exception as e:
        print(f"[Exit] ⚠️ Error limpiando métricas: {e}")

def signal_handler(sig, frame):
    limpiar_pushgateway()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 🧵 Activar hilo en segundo plano
threading.Thread(target=push_metrics, daemon=True).start()
