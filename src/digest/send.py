"""Send the digest email via Gmail SMTP."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_email(
    *,
    sender: str,
    app_password: str,
    recipient: str,
    subject: str,
    html_body: str,
    smtp_factory=smtplib.SMTP_SSL,
) -> None:
    message = MIMEMultipart("alternative")
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtp_factory(SMTP_HOST, SMTP_PORT) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], message.as_string())
