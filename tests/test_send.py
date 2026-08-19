"""Send stage: SMTP interaction via injected factory."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from digest.config import Settings
from digest.send import SMTP_HOST, SMTP_PORT, send_email


def smtp_mock():
    server = MagicMock()
    factory = MagicMock()
    factory.return_value.__enter__ = MagicMock(return_value=server)
    factory.return_value.__exit__ = MagicMock(return_value=False)
    return factory, server


def test_send_email_logs_in_and_sends():
    factory, server = smtp_mock()
    send_email(
        sender="me@gmail.com",
        app_password="secret",
        recipient="me@gmail.com",
        subject="Weekly digest",
        html_body="<p>hi</p>",
        smtp_factory=factory,
    )
    factory.assert_called_once_with(SMTP_HOST, SMTP_PORT)
    server.login.assert_called_once_with("me@gmail.com", "secret")
    (sender, recipients, payload) = server.sendmail.call_args.args
    assert sender == "me@gmail.com"
    assert recipients == ["me@gmail.com"]
    assert "Subject: Weekly digest" in payload
    assert "text/html" in payload


def test_settings_require_email_raises_on_missing(monkeypatch):
    monkeypatch.delenv("GMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="GMAIL_ADDRESS"):
        Settings().require_email()


def test_settings_recipient_defaults_to_sender(monkeypatch):
    monkeypatch.setenv("GMAIL_ADDRESS", "me@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "pw")
    monkeypatch.delenv("DIGEST_TO", raising=False)
    assert Settings().digest_to == "me@gmail.com"
