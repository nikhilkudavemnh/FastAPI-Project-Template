"""Worker entrypoint placeholder. When TASK_BACKEND=celery is wired, replace the body with:

from app.tasks.backends.celery_backend import celery_app
celery_app.worker_main(["worker", "--loglevel=INFO"])
"""

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    get_logger(__name__).error(
        "no_worker_backend",
        task_backend=settings.task_backend,
        hint="Enable a real backend in app/tasks/backends/ and update app/worker.py",
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
