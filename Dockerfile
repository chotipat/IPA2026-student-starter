FROM python:3.12-slim

WORKDIR /opt/ipa2026

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WEBHOOK_HOST=0.0.0.0 \
    WEBHOOK_PORT=8000

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY ansible/ ./ansible/

EXPOSE 8000
CMD ["python", "-m", "app.webhook_server"]
