# Image DomoPi (usage optionnel, voir docker-compose.yml)
FROM python:3.12-slim-bookworm

WORKDIR /app

# Dependances systeme minimales (compilation cryptographie HAP)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 51826
CMD ["python", "main.py"]
