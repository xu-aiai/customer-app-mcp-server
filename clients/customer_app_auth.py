import json
import logging
from urllib import error, parse, request

from clients.customer_app_config import (
    load_customer_app_config,
    update_customer_app_token,
)

logger = logging.getLogger("CustomerAppAuth")


def extract_access_token(response_data: dict) -> str:
    candidates = [
        response_data.get("access_token"),
        response_data.get("token"),
        (response_data.get("data") or {}).get("access_token")
        if isinstance(response_data.get("data"), dict)
        else None,
        (response_data.get("data") or {}).get("token")
        if isinstance(response_data.get("data"), dict)
        else None,
    ]
    for token in candidates:
        if token:
            return token
    raise RuntimeError("Token response does not contain access_token or token.")


def fetch_customer_app_token(timeout: int = 30) -> str:
    config = load_customer_app_config()
    auth_config = config.get("auth") or {}
    auth_base_url = (config.get("auth_base_url") or "").rstrip("/")
    token_url = f"{auth_base_url}/oauth/token"

    payload = {
        "username": auth_config.get("username"),
        "password": auth_config.get("password"),
        "scope": auth_config.get("scope", "server"),
        "grant_type": auth_config.get("grant_type", "password"),
    }
    missing_fields = [key for key, value in payload.items() if not value]
    if missing_fields:
        raise RuntimeError(f"Missing auth config fields: {', '.join(missing_fields)}")

    headers = {
        "Authorization": auth_config.get("authorization", ""),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    if not headers["Authorization"]:
        raise RuntimeError("Missing auth.authorization in customer app config.")

    encoded_payload = parse.urlencode(payload).encode("utf-8")
    token_request = request.Request(
        token_url,
        data=encoded_payload,
        headers=headers,
        method="POST",
    )

    logger.info(
        "Requesting customer app token: url=%s username=%s",
        token_url,
        payload["username"],
    )
    try:
        with request.urlopen(token_request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            logger.info(
                "Customer app token response received: status=%s bytes=%s",
                response.status,
                len(response_body.encode("utf-8")),
            )
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Token request failed: status={exc.code} body={response_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Token request failed: reason={exc.reason}") from exc

    response_data = json.loads(response_body)
    token = extract_access_token(response_data)
    update_customer_app_token(token)
    logger.info("Customer app token saved to config/customer_app_config.json")
    return token
