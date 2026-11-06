"""Example tasks. Import this module (see main.py) so they register at startup."""

from app.core.logging import get_logger
from app.tasks import task

log = get_logger(__name__)


@task("users.send_welcome_email")
async def send_welcome_email(user_id: str, email: str) -> None:
    # Replace with a real mail provider; this is a placeholder.
    log.info("welcome_email_sent", user_id=user_id, email=email)
