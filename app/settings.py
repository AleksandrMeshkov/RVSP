from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _split_emails(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class MailSettings:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_to: list[str]
    smtp_starttls: bool

    @property
    def is_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_port and self.smtp_from and self.smtp_to)


def get_mail_settings() -> MailSettings:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = _to_int(os.getenv("SMTP_PORT"), 587)
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM", "").strip() or smtp_user
    smtp_to = _split_emails(os.getenv("SMTP_TO"))
    smtp_starttls = _to_bool(os.getenv("SMTP_STARTTLS"), True)

    return MailSettings(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_from=smtp_from,
        smtp_to=smtp_to,
        smtp_starttls=smtp_starttls,
    )
