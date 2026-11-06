import asyncio

from httpx import AsyncClient

from app.tasks import enqueue, get_backend, registry, task
from app.tasks.backends.inline import InlineBackend


async def test_ai_chat_echo(client: AsyncClient, user_headers: dict[str, str]) -> None:
    r = await client.get("/api/v1/ai/providers", headers=user_headers)
    assert r.json() == ["echo"]
    r = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
        headers=user_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["text"] == "echo: hello"


async def test_ai_requires_auth(client: AsyncClient) -> None:
    r = await client.post("/api/v1/ai/chat", json={"messages": [{"role": "user", "content": "x"}]})
    assert r.status_code == 401


async def test_inline_task_backend(client: AsyncClient) -> None:
    done = asyncio.Event()
    seen: list[int] = []

    if "tests.ping" not in registry.names():

        @task("tests.ping")
        async def ping(n: int) -> None:
            seen.append(n)
            done.set()

    handle = await enqueue("tests.ping", n=42)
    assert handle.backend == "inline"
    backend = get_backend()
    assert isinstance(backend, InlineBackend)
    await backend.drain()
    assert seen == [42] and done.is_set()
