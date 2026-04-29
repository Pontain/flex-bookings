import os
from email.message import EmailMessage

import aiosmtplib


async def send_password_reset_email(to_email: str, reset_link: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    from_name = os.getenv("SMTP_FROM_NAME", "FlexBooking")

    print("SMTP_HOST:", smtp_host)
    print("SMTP_PORT:", smtp_port)
    print("SMTP_USERNAME:", smtp_username)
    print("SMTP_FROM_EMAIL:", from_email)
    print("SKICKAR TILL:", to_email)

    if not all([smtp_host, smtp_username, smtp_password, from_email]):
        print("SMTP saknar inställningar. Reset-länk:", reset_link)
        return

    message = EmailMessage()
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message["Subject"] = "Återställ ditt lösenord"

    message.set_content(f"""
    Hej!

    Klicka på länken nedan för att återställa ditt lösenord:
    {reset_link}
    """)

    message.add_alternative(f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f6f8; padding:20px;">
        <div style="max-width:500px; margin:auto; background:white; padding:30px; border-radius:10px;">
        
        <h2 style="margin-top:0;">Återställ lösenord</h2>
        
        <p>Du har begärt att återställa ditt lösenord.</p>
        
        <p style="text-align:center; margin:30px 0;">
            <a href="{reset_link}" 
            style="background:#3b82f6; color:white; padding:12px 20px; 
                    text-decoration:none; border-radius:6px; font-weight:bold;">
            Återställ lösenord
            </a>
        </p>

        <p style="font-size:14px; color:#555;">
            Länken är giltig i 1 timme.
        </p>

        <p style="font-size:12px; color:#999;">
            Om du inte begärt detta kan du ignorera detta mail.
        </p>

        </div>
    </body>
    </html>
    """, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            start_tls=True,
        )
        print("MAIL SKICKAT ✅")
    except Exception as e:
        print("MAIL FEL ❌:", repr(e))