# Image officielle Python 3.12 slim
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances système requises (PostgreSQL, build tools, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du script d'entrée et correction des fins de ligne (CRLF -> LF)
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Copie du code source
COPY . /app/

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# Par défaut, serveur de développement avec reload et écoute sur 0.0.0.0
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
