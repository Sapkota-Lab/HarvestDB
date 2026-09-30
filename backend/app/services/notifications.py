from bird import APIError, Bird
from app.core.config import settings
from app.core.logging_config import logger
from datetime import datetime, timedelta, timezone

class NotificationService:
    def __init__(self):
        self.alert_cooldown = timedelta(minutes=15)
        self.last_alert_time: datetime | None = None

    def send_critical_alert(
        self,
        subject: str,
        message: str,
    ) -> bool:

        # Notification system can be disabled through .env
        if not settings.email_alerts:
            return False

        now = datetime.now(timezone.utc)

        # Prevent repeated emails during an ongoing problem
        if (
            self.last_alert_time is not None
            and now - self.last_alert_time < self.alert_cooldown
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
                        <p>
                            Please check the application
                            and database status.
                        </p>
                    """,
                )

            self.last_alert_time = now

            logger.info(
                "Critical alert email accepted by Bird. Message ID: %s",
                email.id,
            )

            return True

        except APIError as error:
            logger.error(
                "Failed to send critical alert email: %s",
                error,
            )
            return False


notification_service = NotificationService()