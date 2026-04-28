import http.client
import json
import os
import urllib.parse

from dotenv import load_dotenv

from config import REQUEST_TIMEOUT_SECONDS

load_dotenv()


def send_tg_notification(message: str) -> bool:
    """Send Telegram notification."""
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not telegram_token or not telegram_chat_id:
        print("Telegram configuration is incomplete, cannot send notification", flush=True)
        return False

    params = urllib.parse.urlencode({"chat_id": telegram_chat_id, "text": message})
    conn = http.client.HTTPSConnection("api.telegram.org", timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        conn.request("GET", f"/bot{telegram_token}/sendMessage?{params}")
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        result = json.loads(data)

        if response.status == 200 and result.get("ok"):
            print("Notification sent successfully", flush=True)
            return True

        print(f"Notification sent failed: {response.status} - {data}", flush=True)
        return False

    except Exception as e:
        print(f"Notification sending process error: {e}", flush=True)
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    send_tg_notification("Action test")
