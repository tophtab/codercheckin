import json


_ALREADY_CHECKED_IN_MESSAGES = (
    "今天已完成签到",
    "今日已完成签到",
    "今天已经签到",
    "今日已经签到",
    "already checked in",
    "already signed",
)


def is_successful_checkin_response(status_code: int, response_text: str) -> bool:
    payload = _extract_payload(response_text)
    if isinstance(payload, dict):
        success = payload.get("success")
        if isinstance(success, bool):
            return success or _message_means_already_checked_in(payload, response_text)

    if status_code == 200:
        return True

    return _message_means_already_checked_in(payload, response_text)


def _message_means_already_checked_in(payload, response_text: str) -> bool:
    message = _extract_message(payload, response_text)
    normalized = message.lower()
    return any(keyword in normalized for keyword in _ALREADY_CHECKED_IN_MESSAGES)


def _extract_payload(response_text: str):
    try:
        return json.loads(response_text)
    except ValueError:
        return None


def _extract_message(payload, response_text: str) -> str:
    if payload is None:
        return response_text

    if not isinstance(payload, dict):
        return response_text

    message = payload.get("message") or payload.get("msg") or response_text
    return str(message)
