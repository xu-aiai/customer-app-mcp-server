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
            raise ValueError(body.get("error") or "Service order request failed.")
        if body.get("ok") is not True or body.get("code") != 0:
            raise ValueError(
                "Service order API failed: "
                f"code={body.get('code')} msg={body.get('msg')}"
            )
