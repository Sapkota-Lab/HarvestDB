from app.services.notifications import notification_service
from unittest.mock import patch

from app.core.logging_config import handle_error


def test_noncritical_error_does_not_send_alert(): #Mock testing to ensure that non-critical errors do not trigger the send_critical_alert function.
    with patch(
        "app.core.logging_config.notification_service.send_critical_alert"
    ) as mock_alert:
        
        handle_error(
            level="WARNING",
            message="This is a noncritical warning."
        )
        mock_alert.assert_not_called()

def test_send_critical_alert(): #Will send emails if errors are critical 

    result = notification_service.send_critical_alert(
        subject="HarvestDB Test Alert",
        message="This is a test of the HarvestDB critical error email system.",
    )
    assert result is True

def test_send_critical_alert_with_long_message(): #Linger messages are sent 
    message = "HarvestDB test message. " * 50

    result = notification_service.send_critical_alert(
        subject="HarvestDB Long Message Test",
        message=message,
    )
    assert result is True