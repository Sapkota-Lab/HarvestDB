from bird import APIError, Bird
from app.core.config import settings
from app.core.logging_config import logger
from datetime import datetime, timedelta, timezone

ALERT_COOLDOWN = timedelta(minutes=15) # change as needed for testing purposes
last_alert_time: datetime | None = None

def send_critical_alert(subject: str, message: str) -> bool:
    global last_alert_time

    if not settings.email_alerts: # Notificaion system disabled in env
        return False

    now = datetime.now(timezone.utc)

    if (
        last_alert_time is not None
        and now - last_alert_time < ALERT_COOLDOWN # Prevent sending multiple emails within the cooldown period
    ):
        logger.info(
            "Critical email alert skipped because cooldown is active."
        )
        return False

    try:
        with Bird(api_key=settings.bird_api_key) as client:
            email = client.email.send(
                from_={
                    "email": "onboarding@messagebird.dev",
                    "name": "HarvestDB Alerts",
                },
                to=[settings.alert_email_to],
                subject=subject,
                html=f"""
                    <h2>HarvestDB Critical Error</h2>
                    <p>{message}</p>
                    <p>Please check the application and database status.</p>
                """,
            )

        last_alert_time = now

        logger.info(
            "Critical alert email accepted by Bird. Message ID: %s",
            email.id,
        )

        return True
    # IMPORTANT: BIRD API limits to 50 emails per day, 1000 emails per month. If you exceed this limit, the API will return a 429 error.
    except APIError as error:
        logger.error(
            "Failed to send critical alert email: %s",
            error,
        )
        return False