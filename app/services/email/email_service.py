import logging

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    async def send_activation_email(
        to_email: str,
        username: str,
        password: str,
        activation_token: str
    ):
        activation_link = f"{settings.FRONTEND_URL}/activate?token={activation_token}"

        html_content = f"""
        <h2>Activacion de cuenta</h2>
        <p>Hola,</p>
        <p>Tu cuenta ha sido creada.</p>

        <p><strong>Usuario:</strong> {username}</p>
        <p><strong>Contrasena inicial:</strong> {password}</p>
        <p><a href="{activation_link}">Activar cuenta</a></p>
        """

        payload = {
            "sender": {
                "name": settings.BREVO_SENDER_NAME,
                "email": settings.MAIL_FROM,
            },
            "to": [{"email": to_email}],
            "subject": "Activacion de cuenta",
            "htmlContent": html_content,
        }

        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        }

        try:
            if not settings.BREVO_API_KEY:
                raise ValueError("BREVO_API_KEY is not configured")

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    settings.BREVO_API_URL,
                    json=payload,
                    headers=headers,
                )
                if response.is_error:
                    logger.error(
                        "Brevo rejected activation email to %s with status %s: %s",
                        to_email,
                        response.status_code,
                        response.text,
                    )
                response.raise_for_status()
        except Exception:
            logger.exception("Could not send activation email to %s", to_email)
