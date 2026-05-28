from fastapi_mail import FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.core.mail.mail_config import mail_config



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
        <h2>Activación de cuenta</h2>
        <p>Hola,</p>
        <p>Tu cuenta ha sido creada.</p>

        <p><strong>Usuario:</strong> {username}</p>
        <p><strong>Contraseña inicial:</strong> {password}</p>

        """
        
        message = MessageSchema(
            subject="Activación de cuenta",
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(mail_config)
        await fm.send_message(message)
