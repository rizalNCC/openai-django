# Django 3.2 + Docker (SQLite)

A Django project running with **Django 3.2.25**, **Python 3.10**, and **Docker Compose v2**.  
The default database is **SQLite**, so the project can run immediately without setting up a database server.

This setup is suitable for:

- Local development
- Prototyping
- Learning Django with Docker

---

## Tech Stack

- Python: 3.10
- Django: 3.2.25
- Database: SQLite
- Docker: Docker Desktop (Compose v2)
- **OpenAI SDK**: 2.17.0
- **Django Rest Framework**: 3.15.1
- **Swagger UI**: via drf-yasg

---

## Features

- **OpenAI Integration**: Ready to use `openai` python library.
- **API Documentation**: Automated Swagger UI.

## Usage

### Run Project
```bash
docker-compose up
```

### Access
- **Web App**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/swagger/
- **Redoc**: http://localhost:8000/redoc/


---
