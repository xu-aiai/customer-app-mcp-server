import json
from json import JSONDecodeError
from typing import Optional

from clients.customer_app import CustomerAppClient, REQUEST_TIMEOUT_SECONDS


class ServiceOrderClient:
    """Client for serviceOrderUnion work order APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_base_url: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.customer_app_client = CustomerAppClient(
            base_url=base_url,
            service_base_url=service_base_url,
            timeout=timeout,
        )

    def fetch_orders(
        self,
        app_token: Optional[str] = None,
        vincode: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 3,
        language: Optional[str] = None,
    ) -> list[dict]:
        """Fetch a page of current user's service orders.

        GET /ixcmg/serviceOrderUnion/getPage
        """
        params = {
            "pageNum": page_num,
            "pageSize": page_size,
        }
        if vincode:
            params["deviceVin"] = vincode

        body = self.customer_app_client.call_service_order_union(
            endpoint="getPage",
            method="GET",
            token=app_token,
            language=language,
            params=params,
        )
        self._ensure_success(body)
        data = body.get("data") or {}
        return data.get("records") or []

    def fetch_order_detail(
        self,
        order_id: str,
        app_token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """Fetch a single service order detail.

        GET /ixcmg/serviceOrderUnion/{order_id}
        """
        body = self.customer_app_client.call_service_order_union(
            endpoint=str(order_id).strip(),
            method="GET",
            token=app_token,
            language=language,
        )
        self._ensure_success(body)
        record = body.get("data")
        if not record:
            raise ValueError("Service order not found.")
        if not isinstance(record, dict):
            raise ValueError("Service order detail response data is not an object.")
        return record

    def _ensure_success(self, body: dict) -> None:
        if body.get("success") is False:
            raise ValueError(self._format_failure(body))
        if body.get("ok") is not True or body.get("code") != 0:
            raise ValueError(
                "Service order API failed: "
                f"code={body.get('code')} msg={body.get('msg')}"
            )

    def _format_failure(self, body: dict) -> str:
        raw_error = body.get("error") or body.get("message") or body.get("msg")
        parsed_error = self._parse_json_object(raw_error)
        if parsed_error:
            parts = [
                "Service order API failed",
                f"status={parsed_error.get('status')}",
                f"error={parsed_error.get('error')}",
                f"path={parsed_error.get('path')}",
                f"message={parsed_error.get('message')}",
            ]
            return "; ".join(part for part in parts if not part.endswith("=None"))

        status_code = body.get("status_code")
        if status_code:
            return f"Service order API failed: status={status_code} error={raw_error}"
        return str(raw_error or "Service order request failed.")

    def _parse_json_object(self, value) -> Optional[dict]:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return None
        try:
            parsed = json.loads(value)
        except JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None
