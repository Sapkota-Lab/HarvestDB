from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from app.services.notifications import notification_service


def test_send_critical_alert():
    notification_service.last_alert_time = None

    with patch("app.services.notifications.Bird") as mock_bird, \
         patch("app.services.notifications.settings.email_alerts", True):

        mock_client = mock_bird.return_value.__enter__.return_value

        mock_email = MagicMock()
        mock_email.id = "test-message-id"
        mock_client.email.send.return_value = mock_email

        result = notification_service.send_critical_alert(
            subject="HarvestDB Test Alert",
            message="This is a test of the HarvestDB critical error email system.",
        )

        assert result is True
        mock_client.email.send.assert_called_once()


def test_send_critical_alert_with_long_message():
    notification_service.last_alert_time = None

    message = "HarvestDB test message. " * 50

    with patch("app.services.notifications.Bird") as mock_bird, \
         patch("app.services.notifications.settings.email_alerts", True):

        mock_client = mock_bird.return_value.__enter__.return_value

        mock_email = MagicMock()
        mock_email.id = "test-message-id"
        mock_client.email.send.return_value = mock_email

        result = notification_service.send_critical_alert(
            subject="HarvestDB Long Message Test",
            message=message,
        )

        assert result is True
        mock_client.email.send.assert_called_once()

        call_kwargs = mock_client.email.send.call_args.kwargs
        assert message in call_kwargs["html"]

def test_send_critical_alert_disabled():
    notification_service.last_alert_time = None

    with patch("app.services.notifications.Bird") as mock_bird, \
         patch("app.services.notifications.settings.email_alerts", False):

        result = notification_service.send_critical_alert(
            subject="Test Alert",
            message="Test message",
        )

        assert result is False
        mock_bird.assert_not_called()

def test_send_critical_alert_during_cooldown():
    notification_service.last_alert_time = datetime.now(timezone.utc)

    with patch("app.services.notifications.Bird") as mock_bird, \
         patch("app.services.notifications.settings.email_alerts", True):

        result = notification_service.send_critical_alert(
            subject="Test Alert",
            message="Test message",
        )

        assert result is False
        mock_bird.assert_not_called()

    notification_service.last_alert_time = None