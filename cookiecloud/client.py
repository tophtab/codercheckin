import os
from urllib.parse import urlencode, urlparse

import requests


_COOKIE_CLOUD_CACHE = None


def get_cookie_value(env_name: str, domains: list[str]) -> str:
    """Resolve a cookie from direct env config or Cookie Cloud."""
    direct_cookie = os.environ.get(env_name, "").strip()
    if direct_cookie:
        return direct_cookie

    cookie = _get_cookiecloud_cookie(domains)
    if cookie:
        print(f"{env_name} loaded from Cookie Cloud", flush=True)
    return cookie


def _get_cookiecloud_cookie(domains: list[str]) -> str:
    payload = _fetch_cookiecloud_payload()
    if not payload:
        return ""

    cookie_data = payload.get("cookie_data")
    if not isinstance(cookie_data, dict):
        print("Cookie Cloud payload does not contain cookie_data", flush=True)
        return ""

    matched_hosts = _find_matching_hosts(cookie_data, domains)
    if not matched_hosts:
        print(
            f"Cookie Cloud did not return cookies for domains: {', '.join(domains)}",
            flush=True,
        )
        return ""

    merged = {}
    for host in matched_hosts:
        for item in cookie_data.get(host, []):
            name = str(item.get("name", "")).strip()
            value = str(item.get("value", ""))
            if name:
                merged[name] = value

    return "; ".join(f"{name}={value}" for name, value in merged.items())


def _fetch_cookiecloud_payload():
    global _COOKIE_CLOUD_CACHE
    if _COOKIE_CLOUD_CACHE is not None:
        return _COOKIE_CLOUD_CACHE

    url = os.environ.get("COOKIE_CLOUD_URL", "").strip().rstrip("/")
    uuid = os.environ.get("COOKIE_CLOUD_UUID", "").strip()
    password = os.environ.get("COOKIE_CLOUD_PASSWORD", "").strip()
    crypto_type = os.environ.get("COOKIE_CLOUD_CRYPTO_TYPE", "").strip()

    if not url or not uuid or not password:
        return None

    query = ""
    if crypto_type:
        query = f"?{urlencode({'crypto_type': crypto_type})}"

    endpoint = f"{url}/get/{uuid}{query}"

    try:
        response = requests.post(endpoint, json={"password": password}, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        print(f"Cookie Cloud request failed: {exc}", flush=True)
        return None
    except ValueError as exc:
        print(f"Cookie Cloud returned invalid JSON: {exc}", flush=True)
        return None

    if not isinstance(payload, dict):
        print("Cookie Cloud payload is not a JSON object", flush=True)
        return None

    _COOKIE_CLOUD_CACHE = payload
    return payload


def _find_matching_hosts(cookie_data: dict, domains: list[str]) -> list[str]:
    normalized_domains = [_normalize_domain(domain) for domain in domains]
    matches = []

    for host in cookie_data.keys():
        normalized_host = _normalize_domain(host)
        if any(_domain_matches(normalized_host, domain) for domain in normalized_domains):
            matches.append(host)

    return matches


def _domain_matches(host: str, domain: str) -> bool:
    return (
        host == domain
        or host.endswith(f".{domain}")
        or domain.endswith(f".{host}")
    )


def _normalize_domain(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"//{value}")
    host = parsed.netloc or parsed.path
    return host.split(":", 1)[0].lstrip(".").lower()

