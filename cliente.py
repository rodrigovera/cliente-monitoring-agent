from fastapi import FastAPI, Request
import psutil
import logging
from datetime import datetime
import threading
import time
import requests
from fastapi.responses import Response  # ✅ Necesario para metrics_prometheus
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

app = FastAPI()

# Variables de configuración
PUSHGATEWAY_URL = "http://20.55.80.149:9091"
INSTANCE = "cliente"

# Contador global para que el middleware también lo use
http_requests_total_counter = Counter(
    "http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "endpoint", "instance"]
)

# Middleware para contar cada petición HTTP
@app.middleware("http")
async def contar_http_requests(request: Request, call_next):
    response = await call_next(request)
    http_requests_total_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        instance=INSTANCE
    ).inc()
    return response

# Configura logs en formato JSON y en archivo
logging.basicConfig(
    filename="errors.json",
    level=logging.ERROR,
    format='{"timestamp": "%(asctime)s", "error": "%(message)s"}'
)

# Endpoint de métricas numéricas básicas (solo FastAPI)
@app.get("/metrics")
def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

# Endpoint de métricas en formato Prometheus
@app.get("/metrics_prometheus")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Endpoint que genera un error intencional
@app.get("/causar_error")
def causar_error():
    try:
        raise ValueError("Esto es un error simulado desde el CLIENTE")
    except Exception as e:
        logging.error(str(e))
        raise

# Hilo para empujar métricas al Push Gateway
def push_metrics():
    registry = CollectorRegistry()

    # Registrar métricas dentro del nuevo registro
    cpu_gauge = Gauge("cpu_percent", "CPU usage (%)", ["instance"], registry=registry)
    mem_gauge = Gauge("memory_percent", "RAM usage (%)", ["instance"], registry=registry)
    disk_gauge = Gauge("disk_usage", "Disk usage (%)", ["instance"], registry=registry)

    # Registrar el contador global en el registro personalizado
    registry.register(http_requests_total_counter)

    # Inicializa al menos una etiqueta para que Prometheus la vea aunque no haya tráfico
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
            print("🔍 MÉTRICAS REGISTRY ENVIADAS:\n" + generate_latest(registry).decode("utf-8"))
            push_to_gateway(
                PUSHGATEWAY_URL.replace("http://", ""),
                job=INSTANCE,
                registry=registry
            )

            print("[Push] Métricas empujadas correctamente")
        except Exception as e:
            print(f"[Push] Error al enviar métricas: {e}")
        time.sleep(15)

# Iniciar el hilo en segundo plano
threading.Thread(target=push_metrics, daemon=True).start()

