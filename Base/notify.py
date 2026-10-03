import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def send_contact_email(contact):
    """Email a new contact-form submission via the Resend HTTP API.

    Uses HTTPS rather than SMTP because Render's free tier blocks outbound
    SMTP ports. Configured with environment variables:
      RESEND_API_KEY  - API key from resend.com (required, otherwise skipped)
      CONTACT_EMAIL   - address that receives the messages
      CONTACT_FROM    - sender (default: Resend's shared onboarding address)

    Returns True if the email was accepted, False otherwise. Never raises,
    so a mail problem can't break the form submission.
    """
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("CONTACT_EMAIL")
    if not api_key or not to_email:
        logger.info("Contact email not sent: RESEND_API_KEY or CONTACT_EMAIL not set.")
        return False

    body = (
        f"New message from your portfolio website\n\n"
        f"Name:  {contact.name}\n"
        f"Email: {contact.email}\n"
        f"Phone: {contact.number or '-'}\n\n"
        f"Message:\n{contact.content}\n"
    )
    payload = {
        "from": os.getenv("CONTACT_FROM", "Portfolio <onboarding@resend.dev>"),
        "to": [to_email],
        "reply_to": contact.email,
        "subject": f"Portfolio contact: {contact.name}",
        "text": body,
    }
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "portfolio-website",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError) as exc:
        detail = exc.read().decode(errors="replace") if isinstance(exc, urllib.error.HTTPError) else exc
        logger.error("Failed to send contact email: %s", detail)
        return False
