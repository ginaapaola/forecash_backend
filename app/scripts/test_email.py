import asyncio

from app.core.config import settings

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS
)

async def test():
    message = MessageSchema(
        subject="Correo de prueba",
        recipients=["terryhurtado04@gmail.com"],
        body="<h1>ESTE ES UN MENSAJE DE LA FLACA MÁS HERMOSA QUE CONOCES!</h1><p>Yo también te extraño, quiero verte y que me la metas toda hasta el fondo ❤️😔.</p>",
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    print("CORREO ENVIADO ¡SOS LA PUTA AMA!")

asyncio.run(test())