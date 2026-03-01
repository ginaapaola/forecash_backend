import asyncio

from app.core.config import settings

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.services.email.email_service import EmailService


async def test():
    await EmailService.send_activation_email(
        "ginapao007@gmail.com",
        "username",
        "password",
        "supon que este es tu token :p"
    )
    print("CORREO ENVIADOOO")

asyncio.run(test())