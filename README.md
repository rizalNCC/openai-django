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
- **Admin Dashboard + Playground**: PicoCSS UI for quick management and testing.

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

## Data Model

### Entity Overview

1. **AgentProfile**
   - Defines a chatbot profile: model, system prompt, owner, and default flag.
2. **AgentTool**
   - Describes a tool that can be used by an agent (function/custom).
3. **AgentProfileTool**
   - Many-to-many link between profiles and tools (with `enabled`).
4. **AgentPromptTemplate**
   - Optional reusable prompt templates, optionally scoped to an agent or owner.
5. **AgentSession**
   - A conversation session tied to an agent; stores `previous_response_id` and last model output.
6. **AgentMessage**
   - Conversation messages (user/assistant) linked to a session.

### Tables & Fields

#### `AgentProfile`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(200) | Required |
| `owner` | FK → AUTH_USER | Nullable |
| `model` | CharField(100) | Default `gpt-4.1` |
| `system_prompt` | TextField | Optional |
| `is_default` | Boolean | Default `false` |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

#### `AgentTool`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(120) | Unique |
| `description` | TextField | Optional |
| `tool_type` | CharField | `function` \| `custom` |
| `parameters` | JSONField | Function schema |
| `is_active` | Boolean | Default `true` |
| `created_at` | DateTime | Auto |

#### `AgentProfileTool`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `agent` | FK → AgentProfile | Required |
| `tool` | FK → AgentTool | Required |
| `enabled` | Boolean | Default `true` |
| **Constraints** |  | `unique_together(agent, tool)` |

#### `AgentPromptTemplate`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(200) | Required |
| `template` | TextField | Required |
| `owner` | FK → AUTH_USER | Nullable |
| `agent` | FK → AgentProfile | Nullable |
| `is_default` | Boolean | Default `false` |
| `created_at` | DateTime | Auto |

**Template scope behavior**
- If `agent` is set, the template is scoped to that agent.
- If `agent` is null, the template is **global** and can apply to all agents.
- When building instructions, agent-scoped templates take priority; if none exist, global templates are used.

#### `AgentSession`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `agent` | FK → AgentProfile | Required |
| `owner` | FK → AUTH_USER | Nullable |
| `previous_response_id` | CharField(200) | OpenAI response linkage |
| `last_output` | JSONField | Cached model output |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

#### `AgentMessage`
| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `session` | FK → AgentSession | Required |
| `role` | CharField(20) | `user` \| `assistant` |
| `content` | TextField | Message text |
| `created_at` | DateTime | Auto |

### Relationships

- **AgentProfile 1 ↔ N AgentSession**
- **AgentSession 1 ↔ N AgentMessage**
- **AgentProfile N ↔ N AgentTool** (via `AgentProfileTool`)
- **AgentProfile 1 ↔ N AgentPromptTemplate** (optional)
- **User 1 ↔ N AgentProfile / AgentSession / AgentPromptTemplate** (optional)

### Schema Diagram (Text)

```
User
  ├─< AgentProfile >─┐
  │                 ├─< AgentProfileTool >─ AgentTool
  ├─< AgentSession >─┬─< AgentMessage
  └─< AgentPromptTemplate
```

---

## First‑Run Use Case (Empty Database)

If the database is empty, the easiest path is through Django Admin. This lets non-developers create a working agent without using the API or CLI.

1. **Run migrations (once)**
   ```bash
   docker compose run --rm django python manage.py migrate
   ```

2. **Create an Agent Profile**
   - Open Django Admin: `http://localhost:8000/admin/`
   - Go to **Agent Profiles** → **Add**
   - Fill in:
     - `Name`: "Default Agent"
     - `Model`: choose a model (e.g., `gpt-4.1`)
     - `System Prompt`: e.g. "You are a helpful assistant."
     - `Is default`: ✅

3. **(Optional) Create a Tool**
   - Go to **Agent Tools** → **Add**
   - Set:
     - `Name`: e.g. `echo`
     - `Tool type`: `function`
     - `Parameters`: JSON schema for tool args
     - `Is active`: ✅

4. **(Optional) Create a Prompt Template**
   - Go to **Agent Prompt Templates** → **Add**
   - Set:
     - `Name`: e.g. "Support Template"
     - `Template`: your reusable prompt text
     - `Agent` (optional): pick a specific agent or leave blank for global use
     - `Is default`: optional

5. **(Optional) Link Tool to Agent**
   - Go to **Agent Profile Tools** → **Add**
   - Select the agent and the tool, enable it

6. **Start Chatting**
   - Use the playground: `http://localhost:8000/playground/`
   - Select your agent profile and send a message

---
