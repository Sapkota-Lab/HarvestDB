from app.services.notifications import send_critical_alert


result = send_critical_alert(
    subject="HarvestDB Test Alert",
    message="This is a test of the HarvestDB critical error email system.",
)

print("Email sent:", result)