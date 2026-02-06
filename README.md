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
- **Agent Profiles & Tools**: CRUD endpoints and Django admin to manage prompts, models, and tools.
- **Streaming Agent API**: Server-Sent Events (SSE) streaming with tool-call handling.

## Usage

### Run Project
```bash
docker compose up
```

### Run Migrations
```bash
docker compose run --rm django python manage.py migrate
```

### Run Tests
```bash
docker compose run --rm django python manage.py test
```

### Access
- **Web App**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/swagger/
- **Redoc**: http://localhost:8000/redoc/
- **Admin Dashboard**: http://localhost:8000/dashboard/
- **Agent Playground**: http://localhost:8000/playground/

---

## API Overview

### Agent Streaming (SSE)

POST `/api/agent/stream/`

Request:
```json
{
  "message": "Hello",
  "agent_id": 1,
  "session_id": 1,
  "auto_execute_tools": false
}
```

Response:
- `text/event-stream` with events:
  - `openai_event` (raw OpenAI streaming events)
  - `text_delta` (convenience text chunks)
  - `done` (includes `session_id`)

### Tool Output Continuation (SSE)

POST `/api/agent/tool-output/`

Request:
```json
{
  "session_id": 1,
  "call_id": "call_123",
  "output": "{\"result\": \"ok\"}"
}
```

### CRUD Endpoints

- Agent Profiles: `/api/agents/`
- Agent Tools: `/api/tools/`

### Agent Chat (Non-Streaming)

POST `/api/agent/chat/`

Request:
```json
{
  "message": "Hello",
  "agent_id": 1,
  "session_id": 1
}
```

### Admin

Use Django admin to manage agent profiles, tools, sessions, messages, and prompt templates.

### Playground

Use `/playground/` to simulate streaming requests and tool-output continuation without a separate frontend.

---
