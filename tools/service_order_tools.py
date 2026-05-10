from typing import Optional

from clients.service_order import ServiceOrderClient
from i18n import t

COMPACT_FIELDS = (
    "id",
    "crmOrderId",
    "unionOrderNo",
    "crmServiceOrderNo",
    "status",
    "orderType",
    "isShutdown",
    "sourceChannel",
    "deviceModel",
    "deviceVin",
    "deviceName",
    "contactName",
    "contactPhone",
    "memberName",
    "faultDescription",
    "detailAddress",
    "deviceProvinceName",
    "deviceCityName",
    "deviceRegionName",
    "createTime",
    "firstTime",
    "pushOrderTime",
    "pushWorkTime",
    "acceptTime",
    "bookTime",
    "goTime",
    "startServiceTime",
    "finishTime",
    "cancelTime",
    "returnTime",
    "commentTime",
    "serviceUserName",
    "serviceUserPhone",
    "newPlatenumber",
    "newServicemode",
    "maintainCategory",
    "workHours",
    "workMileage",
)

FIXED_VINCODE = "XUGG2154CTKA02713"


def _fixed_vincode() -> str:
    return FIXED_VINCODE


def _error(message: str) -> dict:
    return {
        "success": False,
        "error": message,
    }


def _require(value: Optional[str], name: str, language: Optional[str] = None) -> Optional[dict]:
    if value is None or not str(value).strip():
        return _error(t("common.required", language=language, name=name))
    return None


def _resolve_customer_app_token(
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
) -> Optional[str]:
    """Resolve only customer App tokens.

    Do not accept the generic `token` field here: CRM+ tokens are obtained and
    used only by the CRM+ client when creating work orders.
    """
    return app_token or xcmg_app_token


def _client(
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> ServiceOrderClient:
    return ServiceOrderClient(base_url=base_url, service_base_url=service_base_url)


def _compact_record(record: dict, language: Optional[str] = None) -> dict:
    compact: dict = {}
    for field in COMPACT_FIELDS:
        value = record.get(field)
        if value is None or value == "":
            continue
        compact[field] = value

    status = compact.get("status")
    if isinstance(status, int):
        compact["status_label"] = t(
            f"service_order.status.{status}",
            language=language,
        )
        if compact["status_label"] == f"service_order.status.{status}":
            compact["status_label"] = t(
                "common.unknown_status",
                language=language,
                value=status,
            )

    order_type = compact.get("orderType")
    if isinstance(order_type, int):
        compact["orderType_label"] = t(
            f"service_order.order_type.{order_type}",
            language=language,
        )
        if compact["orderType_label"] == f"service_order.order_type.{order_type}":
            compact["orderType_label"] = t(
                "common.unknown_type",
                language=language,
                value=order_type,
            )

    source_channel = compact.get("sourceChannel")
    if source_channel is not None:
        compact["sourceChannel_label"] = t(
            f"service_order.source_channel.{source_channel}",
            language=language,
        )
        if compact["sourceChannel_label"] == f"service_order.source_channel.{source_channel}":
            compact["sourceChannel_label"] = t(
                "common.unknown_channel",
                language=language,
                value=source_channel,
            )

    shutdown = compact.get("isShutdown")
    if isinstance(shutdown, int):
        compact["isShutdown_label"] = t(
            f"service_order.shutdown.{shutdown}",
            language=language,
        )
        if compact["isShutdown_label"] == f"service_order.shutdown.{shutdown}":
            compact["isShutdown_label"] = t(
                "common.unknown_value",
                language=language,
                value=shutdown,
            )

    service_mode = compact.get("newServicemode")
    if isinstance(service_mode, int):
        compact["newServicemode_label"] = t(
            f"service_order.service_mode.{service_mode}",
            language=language,
        )
        if compact["newServicemode_label"] == f"service_order.service_mode.{service_mode}":
            compact["newServicemode_label"] = t(
                "common.unknown_value",
                language=language,
                value=service_mode,
            )

    return compact


def list_service_orders_tool(
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    vincode: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 3,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """List current user's existing service orders."""
    resolved_token = _resolve_customer_app_token(app_token, xcmg_app_token)

    try:
        records = _client(
            base_url=base_url,
            service_base_url=service_base_url,
        ).fetch_orders(
            app_token=resolved_token,
            vincode=_fixed_vincode(),
            page_num=page_num,
            page_size=page_size,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))

    limited_records = records[:page_size]
    return {
        "success": True,
        "data": {
            "page_num": page_num,
            "page_size": page_size,
            "vincode": _fixed_vincode(),
            "records": [_compact_record(record, language=language) for record in limited_records],
        },
    }


def get_service_order_detail_tool(
    order_id: str,
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """Get one existing service order detail."""
    resolved_token = _resolve_customer_app_token(app_token, xcmg_app_token)
    validation_error = _require(order_id, "order_id", language=language)
    if validation_error:
        return validation_error

    try:
        record = _client(
            base_url=base_url,
            service_base_url=service_base_url,
        ).fetch_order_detail(
            app_token=resolved_token,
            order_id=order_id,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))

    device_vin = str(record.get("deviceVin") or "").strip()
    if device_vin and device_vin != _fixed_vincode():
        return _error(t("service_order.not_belong_to_fixed_device", language=language))

    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "record": _compact_record(record, language=language),
        },
    }
