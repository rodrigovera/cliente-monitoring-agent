FROM python:3.10-slim

WORKDIR /app

# Copiar el script y dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cliente.py .
COPY promtail-config.yml .

# Crear archivo vacío para logs y posiciones
RUN touch errors.json && touch /tmp/positions.yaml

# Puerto expuesto para FastAPI (si lo vas a consultar)
EXPOSE 8000
RUN pip install --no-cache-dir --upgrade prometheus_client
CMD ["uvicorn", "cliente:app", "--host", "0.0.0.0", "--port", "8000"]



