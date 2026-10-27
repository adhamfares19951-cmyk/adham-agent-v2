#!/usr/bin/env python
"""Setup YouTube OAuth token using console flow.
Place your Google OAuth client_secret.json in the project's sessions folder
(C:/Projects/adham-agent/sessions) before running this script.
The script will prompt you for a verification URL and an auth code.
After successful authentication, a persistent token will be saved to
C:/Projects/adham-agent/sessions/youtube_token.json, enabling the
`youtube_upload_video` tool to upload videos.
"""
import os
import sys
from pathlib import Path

# Import the same scopes used by the uploader
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Paths used by the uploader
BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
CLIENT_SECRET_FILE = SESSIONS_DIR / "client_secret.json"
TOKEN_FILE = SESSIONS_DIR / "youtube_token.json"

def main():
    if not CLIENT_SECRET_FILE.is_file():
        print(f"❌ ملف client_secret.json غير موجود في {CLIENT_SECRET_FILE}")
        print("يرجى تحميل ملف OAuth JSON من Google Cloud Console (Credentials → OAuth 2.0 Client IDs) ")
        print("وتسميته client_secret.json ثم وضعه في المجلد المذكور أعلاه.")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("❌ مكتبة google-auth-oauthlib غير مثبتة. تشغيل: pip install google-auth-oauthlib")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    # Use console flow – suitable when لا يمكن فتح المتصفح على الخادم
    creds = flow.run_console()

    # احفظ التوكن في ملف JSON ثابت
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print("✅ تم حفظ توكن YouTube بنجاح في:")
    print(f"   {TOKEN_FILE}")
    print("يمكن الآن رفع الفيديوهات باستخدام أداة youtube_upload_video.")

if __name__ == "__main__":
    main()
