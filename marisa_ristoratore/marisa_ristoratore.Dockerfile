FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY marisa_ristoratore/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY marisa_ristoratore/ .
EXPOSE 5002
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "1", "--threads", "100", "--timeout", "120", "app:app"]
