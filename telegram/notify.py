import http.client
import json
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_SECONDS = 30

def send_tg_notification(message) -> bool:
    """Send Telegram notification
    
    Args:
        message: The message to send
    """
    # Follow https://core.telegram.org/bots/features#botfather to get the bot token.
    telegram_token = os.environ.get('TELEGRAM_TOKEN', '').strip()
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

    if not telegram_token or not telegram_chat_id:
        print("Telegram configuration is incomplete, cannot send notification", flush=True)
        return False
    
    # build the request parameters
    params = urllib.parse.urlencode({
        'chat_id': telegram_chat_id,
        'text': message
    })
    
    # create HTTPS connection
    conn = http.client.HTTPSConnection("api.telegram.org", timeout=REQUEST_TIMEOUT_SECONDS)
    
    try:
        # send GET request
        conn.request(
            "GET", 
            f"/bot{telegram_token}/sendMessage?{params}"
        )
        
        # get response
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        
        # parse JSON response
        result = json.loads(data)
        
        # handle response
        if response.status == 200 and result.get('ok'):
            print("Notification sent successfully", flush=True)
            return True
        else:
            print(f"Notification sent failed: {response.status} - {data}", flush=True)
            return False
            
    except Exception as e:
        print(f"Notification sending process error: {str(e)}", flush=True)
        return False
    finally:
        # ensure connection is closed
        conn.close()

if __name__ == "__main__":
    send_tg_notification("Action test")
