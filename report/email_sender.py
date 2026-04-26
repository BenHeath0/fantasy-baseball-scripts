"""Send a fantasy report via Gmail SMTP."""

import smtplib
from email.message import EmailMessage

from .config import (
    GMAIL_APP_PASSWORD_ENV,
    GMAIL_USER_ENV,
    SMTP_HOST,
    SMTP_PORT,
    get_required_env,
)


def send_email(subject, html_body, to_addr):
    user = get_required_env(GMAIL_USER_ENV)
    password = get_required_env(GMAIL_APP_PASSWORD_ENV)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content("HTML email — please view in an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"Sent report to {to_addr}")
