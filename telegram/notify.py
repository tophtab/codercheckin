import http.client
import json
import os
import urllib.parse

from dotenv import load_dotenv

from config import REQUEST_TIMEOUT_SECONDS
from runtime_log import log

load_dotenv()


def send_tg_notification(message: str) -> bool:
    """Send Telegram notification."""
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not telegram_token or not telegram_chat_id:
        log("Telegram configuration is incomplete, cannot send notification")
        return False

    params = urllib.parse.urlencode({"chat_id": telegram_chat_id, "text": message})
    conn = http.client.HTTPSConnection("api.telegram.org", timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        conn.request("GET", f"/bot{telegram_token}/sendMessage?{params}")
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        result = json.loads(data)

        if response.status == 200 and result.get("ok"):
            log("Notification sent successfully")
            return True

        log(f"Notification sent failed: {response.status} - {data}")
        return False

    except Exception as e:
        log(f"Notification sending process error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    send_tg_notification("Action test")
