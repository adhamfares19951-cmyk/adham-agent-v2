"""One-time Google OAuth login (Gmail + Calendar), then silent token refresh.
Needs credentials.json (downloaded from Google Cloud Console) next to this
file. The first time any Gmail/Calendar tool runs, a browser tab opens for
Adham to log in and approve access; after that, token.json keeps him logged
in automatically (until he revokes access).
"""
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config

log = logging.getLogger("google_auth")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_PATH = config.BASE_DIR / "credentials.json"
TOKEN_PATH = config.BASE_DIR / "token.json"


class GoogleAuthError(Exception):
    """Has a ready Arabic message for the user."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def _get_credentials() -> Credentials:
    if not CREDENTIALS_PATH.exists():
        raise GoogleAuthError(
            "لسا ما ضفت ملف credentials.json (بيانات اعتماد Google) بمجلد المشروع. "
            "اسأل أدهم يحط الملف وبعدين جرب كمان مرة."
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception as e:
            log.warning("Token refresh failed, need a fresh login: %s", e)

    # No valid token yet: run the one-time interactive login (opens a browser tab).
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def gmail_service():
    return build("gmail", "v1", credentials=_get_credentials())


def calendar_service():
    return build("calendar", "v3", credentials=_get_credentials())
