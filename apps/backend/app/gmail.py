import base64
from email.mime.text import MIMEText
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = Path(__file__).parent.parent / "token.json"
CREDENTIALS_PATH = Path(__file__).parent.parent / "credentials.json"


def _get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str) -> tuple[str, str]:
    """Send an email and return (message_id, thread_id)."""
    service = _get_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"], sent["threadId"]


def get_thread_replies(thread_id: str, sent_message_id: str) -> str | None:
    """Return the text of the first reply in the thread after our sent message, or None."""
    service = _get_service()
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = thread.get("messages", [])

    # Find messages after our sent one
    found_sent = False
    for msg in messages:
        if msg["id"] == sent_message_id:
            found_sent = True
            continue
        if found_sent:
            # Extract plain text body
            payload = msg.get("payload", {})
            return _extract_body(payload)

    return None


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""
