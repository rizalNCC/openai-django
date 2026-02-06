FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /requirements/base.txt
RUN pip install --upgrade pip \
    && pip install -r /requirements/base.txt

COPY . /app
