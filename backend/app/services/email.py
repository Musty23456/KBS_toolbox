import smtplib
from email.message import EmailMessage

from app.config import get_settings


settings = get_settings()


def send_password_reset_email(
    to_email: str,
    full_name: str,
    reset_url: str,
) -> None:
    """
    Send a password-reset email using the configured SMTP server.
    """

    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    if not settings.SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_FROM_EMAIL is not configured")

    message = EmailMessage()

    message["Subject"] = "KBS Toolbox - Password Reset"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email

    message.set_content(
        f"""Hello {full_name},

We received a request to reset your KBS Toolbox password.

Click the link below to create a new password:

{reset_url}

This link will expire after {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
KBS Toolbox
"""
    )

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=20,
    ) as server:

        if settings.SMTP_USE_TLS:
            server.starttls()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

        server.send_message(message)
