FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY marisa_rider/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY marisa_rider/ .

EXPOSE 5003

CMD ["python3", "app.py"]
