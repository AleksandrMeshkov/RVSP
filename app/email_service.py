from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib
import ssl
import socket

from app.schemas import RSVPStored
from app.settings import MailSettings


logger = logging.getLogger(__name__)


def _attendance_label(value: bool) -> str:
    return "Да" if value else "Нет"


def _build_message(data: RSVPStored, settings: MailSettings) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Новый ответ Приглашения на свадьбу"
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(settings.smtp_to)

    companion_block = ""
    if data.companion_full_name and data.companion_will_attend is not None:
        companion_block = (
            f"\nСпутник: {data.companion_full_name}\n"
            f"Спутник придет: {_attendance_label(data.companion_will_attend)}\n"
        )

    body = (
        "Получен новый ответ приглашения\n\n"
        f"Гость: {data.full_name}\n"
        f"Присутствие: {_attendance_label(data.will_attend)}\n"
        f"{companion_block}"
        f"Время отправки: {data.created_at.isoformat()}\n"
    )

    msg.set_content(body)
    return msg


def send_rsvp_email(data: RSVPStored, settings: MailSettings) -> None:
    if not settings.is_enabled:
        logger.info("SMTP settings are incomplete. Skip email sending.")
        return

    message = _build_message(data, settings)
    attempts: list[tuple[str, int, bool]] = []

    # Primary attempt from settings.
    attempts.append((settings.smtp_host, settings.smtp_port, settings.smtp_starttls))

    # Gmail/network fallback: if STARTTLS on 587 fails to connect, try SSL 465.
    if settings.smtp_starttls and settings.smtp_port == 587:
        attempts.append((settings.smtp_host, 465, False))

    last_error: Exception | None = None

    for host, port, use_starttls in attempts:
        try:
            if use_starttls:
                with smtplib.SMTP(host, port, timeout=20) as server:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, timeout=20, context=context) as server:
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)

            logger.info(
                "RSVP email sent successfully via %s:%s (%s)",
                host,
                port,
                "STARTTLS" if use_starttls else "SSL",
            )
            return
        except (TimeoutError, socket.timeout, OSError) as exc:
            last_error = exc
            logger.warning(
                "SMTP attempt failed for %s:%s (%s): %s",
                host,
                port,
                "STARTTLS" if use_starttls else "SSL",
                exc,
            )
        except Exception as exc:
            last_error = exc
            logger.exception(
                "SMTP send failed for %s:%s (%s)",
                host,
                port,
                "STARTTLS" if use_starttls else "SSL",
            )

    if last_error is not None:
        logger.error("Failed to send RSVP email after all attempts: %s", last_error)
