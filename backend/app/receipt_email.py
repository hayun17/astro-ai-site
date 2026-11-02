"""Server-side order receipt. Never include card or birth information in email."""
from __future__ import annotations
import os
import smtplib
from email.message import EmailMessage


def receipt_email_ready() -> bool:
    required = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "RECEIPT_FROM_EMAIL", "SUPPORT_EMAIL")
    return all(os.getenv(key, "").strip() for key in required)


def send_payment_receipt(*, to_email: str, product: str, price: str, order_link: str) -> None:
    if not receipt_email_ready():
        raise RuntimeError("Transactional email is not configured")
    if not order_link.startswith("https://"):
        raise ValueError("Receipt URL must be HTTPS")
    message=EmailMessage()
    message["Subject"]="Your AstroMYLA reading is ready ✨"
    message["From"]=os.environ["RECEIPT_FROM_EMAIL"]
    message["To"]=to_email
    message.set_content(
        "Thanks for your purchase!\n\n"
        f"Reading: {product}\nAmount: ₺{price}\n\n"
        "Open this private link to download your paid reading:\n"
        f"{order_link}\n\n"
        "Keep this message. Anyone with the private order link can access your purchased PDF.\n"
        f"Questions or issues? {os.environ['SUPPORT_EMAIL']}\n"
    )
    host=os.environ["SMTP_HOST"]
    port=int(os.environ["SMTP_PORT"])
    with smtplib.SMTP(host,port,timeout=12) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(os.environ["SMTP_USERNAME"],os.environ["SMTP_PASSWORD"])
        server.send_message(message)
