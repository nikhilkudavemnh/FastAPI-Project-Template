# FastAPI Project Template

Microservice-ready FastAPI starter on **Python 3.15**: JWT auth, users + roles/permissions,
a generic async CRUD layer, a pluggable background-task seam (Celery-ready, not wired),
an event-bus seam, and a provider-agnostic AI module you can grow new use cases from.

| Concern        | Choice                                                   |
|----------------|----------------------------------------------------------|
| Runtime        | Python 3.15, uv, FastAPI 0.162, Uvicorn                  |
| Data           | SQLAlchemy 2.1 (async) + asyncpg, Alembic, PostgreSQL 18 |
| Validation     | Pydantic 2.14, pydantic-settings                         |
| Auth           | PyJWT (access + refresh), argon2 via pwdlib              |
| Logging        | structlog (console in dev, JSON in prod), request ids    |
| Tasks          | `app.tasks` registry + `inline` backend; Celery slot     |
| Tooling        | ruff, mypy (strict), pytest + pytest-asyncio, Docker     |

## Quick start

```bash
cp .env.example .env            # edit DATABASE_URL / JWT_SECRET
uv sync                         # creates .venv on Python 3.15
docker compose up -d db redis   # or point DATABASE_URL at your own Postgres
make migrate                    # alembic upgrade head
make seed                       # default roles + first superuser from .env
make dev                        # http://localhost:8000/docs
```

Everything in Docker instead: `make docker-up`.

Run the checks: `make lint`, `make typecheck`, `make test` (tests use in-memory SQLite, no services needed).

## Layout

```
src/app/
├── main.py              # create_app(): wiring only
├── cli.py               # python -m app.cli seed
├── worker.py            # worker entrypoint (stub until a real task backend is enabled)
├── core/                # shared kernel: config, logging, security, exceptions, middleware, pagination
├── db/                  # Base + mixins, async session, generic Repository[M], models registry
├── api/                 # cross-module deps (CurrentUser, require_permissions) + health endpoints
├── modules/             # bounded contexts; each = models + schemas + service + router + module.py
│   ├── auth/            # register / login / refresh / me
│   ├── users/           # CRUD + self endpoints + role assignment
│   ├── roles/           # CRUD; permissions are plain strings ("users:read", "*")
│   └── ai/              # AIProvider protocol + registry + chat/embed use cases
├── tasks/               # task registry, @task decorator, backends/{inline,celery_backend}
└── events/              # EventBus protocol + in-memory impl (swap for Redis/Kafka/NATS)
```

Dependency direction: `router -> service -> repository -> model`. Routers never touch the
session directly beyond passing it to a service. Modules import from `core`, `db`, `api.deps`
and may import each other's *services* (users depends on roles), never each other's routers.

## Monolith or microservices: same image

A **Module** (`app/modules/registry.py`) is a router plus an optional startup hook.
`ENABLED_MODULES` decides which modules a process mounts, so one Docker image deploys as:

```bash
ENABLED_MODULES=auth,users,roles,ai  SERVICE_NAME=api         # monolith
ENABLED_MODULES=auth,users,roles     SERVICE_NAME=identity    # identity service
ENABLED_MODULES=auth,ai              SERVICE_NAME=ai-service  # AI service (auth for token validation)
```

See `docker-compose.yml` for the commented `ai-service` example. All services share
`JWT_SECRET` so tokens issued by one validate in another; `iss` carries the issuing service.
When a service needs its own database, give it its own `DATABASE_URL` and keep only its
models in `app/db/models.py` for that deployment (or split into a separate package later).

## Auth and authorization

- `POST /api/v1/auth/register` creates a user with the `user` role.
- `POST /api/v1/auth/login` (OAuth2 password form) returns access + refresh tokens.
- `POST /api/v1/auth/refresh` rotates the pair. `GET /api/v1/auth/me` returns the caller.
- Guards live in `app/api/deps.py`:

```python
@router.get("/reports", dependencies=[require_permissions("reports:read")])
@router.post("/admin", dependencies=[require_roles("admin")])
async def handler(user: CurrentUser): ...
```

Roles hold a list of permission strings; `"*"` grants all. Superusers bypass every check.
Defaults seeded by `make seed`: `admin` (`*`) and `user` (`users:read_self`, `users:write_self`, `ai:invoke`).

## Adding a module (any new CRUD or AI use case)

1. `mkdir src/app/modules/<name>` with `models.py`, `schemas.py`, `service.py`, `router.py`.
2. Models inherit `UUIDPrimaryKeyMixin, TimestampMixin, Base`. Add them to `app/db/models.py`.
3. `service.py`: subclass `Repository[Model]` (`app/db/repository.py`) and wrap it in a service.
4. `module.py`: `module = Module(name="<name>", router=router, on_startup=optional_fn)`.
5. Add `<name>` to `ENABLED_MODULES`; `make revision m="add <name>"`; `make migrate`.

## Adding an AI use case or provider

- **Provider**: implement `AIProvider` (`complete`, `stream`, `embed`) in
  `app/modules/ai/providers/<vendor>.py`, register it in `app/modules/ai/module.py`.
  The `echo` provider shows the minimal shape and keeps tests dependency-free.
- **Use case**: add a method to `AIService` (summarize, extract, classify, RAG...) or a new
  module that depends on `providers.get()`. Use cases never import vendor SDKs directly.
- Long-running AI jobs should go through `app.tasks` (below) and publish progress via `app.events`.

## Background tasks

```python
from app.tasks import task, enqueue


@task("reports.generate")
async def generate(report_id: str) -> None: ...


await enqueue("reports.generate", report_id="...")
```

`TASK_BACKEND=inline` (default) runs tasks on the event loop in-process: fine for dev,
tests, and light fire-and-forget work. Tasks are registered by *name*, so swapping the
backend changes no task code. To bring in Celery, follow the checklist in
`src/app/tasks/backends/celery_backend.py`, uncomment the `workers` dependency group,
set `TASK_BACKEND=celery`, and enable the `worker` service in `docker-compose.yml`.
The same seam fits arq, Dramatiq, or a cloud queue.

## Error envelope

Every error, from any service, is:

```json
{"error": {"code": "not_found", "message": "User not found", "request_id": "..."}}
```

Raise `NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError` from
`app/core/exceptions.py` inside services. `X-Request-Id` is accepted and echoed on every
response; pass it between services to correlate logs.

## Configuration

All settings come from the environment (`.env` in dev); see `.env.example`. In
`ENVIRONMENT=production`, startup fails if `JWT_SECRET` is default or shorter than 32 chars,
and `/docs` is disabled.
