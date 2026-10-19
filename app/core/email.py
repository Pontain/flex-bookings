import logging, os
from email.message import EmailMessage
import aiosmtplib
logger = logging.getLogger(__name__)
async def send_account_email(to_email, link, purpose):
    host = os.getenv("SMTP_HOST")
    if not host: raise RuntimeError("SMTP är inte konfigurerat; använd lokal SMTP-server vid utveckling.")
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM_EMAIL"]
    message["To"] = to_email
    message["Subject"] = "Modium – " + purpose
    message.set_content(f"{purpose} genom att öppna länken nedan. Länken gäller i en timme.\n\n{link}\n\nOm du inte begärt detta kan du ignorera meddelandet.")
    port = int(os.getenv("SMTP_PORT", "587"))
    await aiosmtplib.send(message, hostname=host, port=port,
        username=os.getenv("SMTP_USERNAME") or None, password=os.getenv("SMTP_PASSWORD") or None,
        use_tls=port == 465, start_tls=port == 587, timeout=15)
