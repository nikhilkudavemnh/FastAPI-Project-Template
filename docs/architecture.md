# Architecture notes

## Request flow

```
client -> RequestContextMiddleware (request id, timing, structlog context)
       -> CORS
       -> router (module)            validates input via Pydantic schemas
       -> deps: get_current_user / require_permissions
       -> service                    business rules, raises AppError subclasses
       -> repository                 SQLAlchemy async, flush only
       -> get_session                commits once per request, rolls back on error
       -> exception handlers         uniform {"error": {...}} envelope
```

## Why this shape supports microservices

- **Shared kernel, not shared app.** `core/`, `db/`, `api/deps.py`, `tasks/`, `events/` are
  the only things every service needs; they have no module imports.
- **Modules are the unit of deployment.** `ENABLED_MODULES` picks what a process mounts.
  Start as a monolith; when a module needs independent scaling, give it its own
  deployment with the same image.
- **Stateless auth.** JWTs are validated locally with the shared secret (switch
  `JWT_ALGORITHM` to RS256 and distribute the public key when you want per-service keys).
- **Async boundaries are already abstract.** `TaskBackend` and `EventBus` are protocols;
  the in-process implementations are stand-ins for Celery/arq and Redis Streams/Kafka/NATS.
- **Uniform observability.** Request id propagation + structured JSON logs + `/health/*`
  endpoints let a gateway or mesh treat every service the same way.

## Splitting a module into its own repo later

1. Copy `src/app/core`, `src/app/db`, `src/app/api/deps.py`, `src/app/tasks`, `src/app/events`
   into a small internal package (e.g. `company-service-kit`) and publish it to your index.
2. The new service depends on that package plus its own `modules/<name>`.
3. Keep the error envelope, health endpoints and request-id header identical.

## Conventions

- One `module.py` per bounded context; it is the only file `main.py` knows about.
- Services receive an `AsyncSession`; they never create engines.
- Repositories `flush()`, never `commit()`.
- Permissions are `"<resource>:<action>"` strings; keep a list per module in its `service.py`.
- Every list endpoint returns `Page[T]`.
