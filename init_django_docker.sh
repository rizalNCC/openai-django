#!/usr/bin/env bash
set -e

PROJECT_NAME=config
DJANGO_VERSION=3.2.25
PYTHON_VERSION=3.10

echo "🚀 Initializing Django $DJANGO_VERSION with Docker (Python $PYTHON_VERSION)"

# ======================
# Folder structure
# ======================
mkdir -p compose/local/django
mkdir -p requirements

# ======================
# requirements/base.txt
# ======================
cat > requirements/base.txt <<EOF
Django==$DJANGO_VERSION
EOF

# ======================
# Dockerfile
# ======================
cat > compose/local/django/Dockerfile <<EOF
FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \\
    && apt-get install -y build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /requirements/base.txt
RUN pip install --upgrade pip \\
    && pip install -r /requirements/base.txt

COPY . /app
EOF

# ======================
# docker-compose.yml
# ======================
cat > docker-compose.yml <<EOF
version: "3.9"

services:
  django:
    build:
      context: .
      dockerfile: compose/local/django/Dockerfile
    container_name: django_app
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    command: python manage.py runserver 0.0.0.0:8000
EOF

# ======================
# Create Django project
# ======================
echo "🐍 Creating Django project..."
docker-compose run --rm django django-admin startproject $PROJECT_NAME .

# ======================
# Run initial migration
# ======================
docker-compose run --rm django python manage.py migrate

echo ""
echo "✅ DONE!"
echo "Run the project with:"
echo "   docker-compose up"
echo ""
echo "Then open:"
echo "   http://localhost:8000"
