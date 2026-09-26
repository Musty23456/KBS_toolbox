import json
from html import escape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings

settings = get_settings()


def send_password_reset_email(
    to_email: str,
    full_name: str,
    reset_url: str,
) -> None:
    """
    Send a password-reset email using the Resend HTTPS API.

    The raw password-reset token is never logged or stored here.
    Resend is accessed over HTTPS, so this does not depend on SMTP
    connectivity from the Render server.
    """

    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured")

    if not settings.RESEND_FROM_EMAIL:
        raise RuntimeError("RESEND_FROM_EMAIL is not configured")

    safe_name = escape(full_name)
    safe_reset_url = escape(reset_url, quote=True)

    text_content = f"""Hello {full_name},

We received a request to reset your KBS Toolbox password.

Click the link below to create a new password:

{reset_url}

This link will expire after {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
KBS Toolbox
"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KBS Toolbox Password Reset</title>
</head>

<body style="
    margin: 0;
    padding: 0;
    background-color: #f5f7fa;
    font-family: Arial, Helvetica, sans-serif;
">

    <div style="
        max-width: 600px;
        margin: 40px auto;
        padding: 20px;
    ">

        <div style="
            background: #ffffff;
            border-radius: 12px;
            padding: 32px;
            border: 1px solid #e5e7eb;
        ">

            <h2 style="
                margin-top: 0;
                color: #111827;
            ">
                KBS Toolbox
            </h2>

            <p style="color: #374151;">
                Hello {safe_name},
            </p>

            <p style="color: #374151; line-height: 1.6;">
                We received a request to reset your KBS Toolbox password.
            </p>

            <p style="color: #374151; line-height: 1.6;">
                Click the button below to create a new password:
            </p>

            <div style="margin: 30px 0;">
                <a
                    href="{safe_reset_url}"
                    style="
                        display: inline-block;
                        padding: 12px 22px;
                        background-color: #2563eb;
                        color: #ffffff;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: bold;
                    "
                >
                    Reset Password
                </a>
            </div>

            <p style="
                color: #6b7280;
                font-size: 14px;
                line-height: 1.6;
            ">
                This link will expire after
                {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.
            </p>

            <p style="
                color: #6b7280;
                font-size: 14px;
                line-height: 1.6;
            ">
                If you did not request a password reset, you can safely
                ignore this email.
            </p>

            <hr style="
                border: 0;
                border-top: 1px solid #e5e7eb;
                margin: 30px 0;
            ">

            <p style="
                color: #9ca3af;
                font-size: 13px;
            ">
                Regards,<br>
                KBS Toolbox
            </p>

        </div>

    </div>

</body>
</html>
"""

    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": "KBS Toolbox - Password Reset",
        "html": html_content,
        "text": text_content,
    }

    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")

            if response.status < 200 or response.status >= 300:
                raise RuntimeError(
                    f"Resend API returned HTTP {response.status}: "
                    f"{response_body}"
                )

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"Resend API error HTTP {exc.code}: {error_body}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to Resend API: {exc.reason}"
        ) from exc
