import os
import smtplib
from email.message import EmailMessage

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


def send_email(to_address, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"[email not configured] To: {to_address}\nSubject: {subject}\n\n{body}")
        return

    message = EmailMessage()
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(message)
