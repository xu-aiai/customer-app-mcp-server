from typing import Optional

from clients.service_order import ServiceOrderClient


STATUS_LABELS: dict[int, str] = {
    0: "待派单",
    1: "待派工",
    2: "待接单",
    3: "待预约",
    4: "待出发",
    5: "行程中",
    6: "服务中",
    7: "已完结",
    8: "已完结",
    10: "待评价",
    100: "已评价",
    500: "已取消",
}

ORDER_TYPE_LABELS: dict[int, str] = {
    1: "维修",
    2: "保养",
}

SOURCE_CHANNEL_LABELS: dict[str, str] = {
    "1": "集团 400",
    "2": "服务站 Portal",
    "3": "铁三角 APP",
    "4": "物联网",
    "5": "CRM+",
    "6": "系统自动",
    "7": "客户 APP",
    "8": "集团客户 APP",
}

SHUTDOWN_LABELS: dict[int, str] = {0: "否", 1: "是"}

SERVICE_MODE_LABELS: dict[int, str] = {
    1: "现场上门指导",
    2: "远程指导",
}

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


def _error(message: str) -> dict:
    return {
        "success": False,
        "error": message,
    }


def _require(value: Optional[str], name: str) -> Optional[dict]:
    if value is None or not str(value).strip():
        return _error(f"{name} is required.")
    return None


def _resolve_token(
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    token: Optional[str] = None,
) -> Optional[str]:
    return app_token or xcmg_app_token or token


def _client(
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> ServiceOrderClient:
    return ServiceOrderClient(base_url=base_url, service_base_url=service_base_url)


def _compact_record(record: dict) -> dict:
    compact: dict = {}
    for field in COMPACT_FIELDS:
        value = record.get(field)
        if value is None or value == "":
            continue
        compact[field] = value

    status = compact.get("status")
    if isinstance(status, int):
        compact["status_label"] = STATUS_LABELS.get(status, f"未知状态({status})")

    order_type = compact.get("orderType")
    if isinstance(order_type, int):
        compact["orderType_label"] = ORDER_TYPE_LABELS.get(
            order_type,
            f"未知类型({order_type})",
        )

    source_channel = compact.get("sourceChannel")
    if source_channel is not None:
        compact["sourceChannel_label"] = SOURCE_CHANNEL_LABELS.get(
            str(source_channel),
            f"未知渠道({source_channel})",
        )

    shutdown = compact.get("isShutdown")
    if isinstance(shutdown, int):
        compact["isShutdown_label"] = SHUTDOWN_LABELS.get(
            shutdown,
            f"未知({shutdown})",
        )

    service_mode = compact.get("newServicemode")
    if isinstance(service_mode, int):
        compact["newServicemode_label"] = SERVICE_MODE_LABELS.get(
            service_mode,
            f"未知({service_mode})",
        )

    return compact


def list_service_orders_tool(
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    vincode: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 3,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """List current user's existing service orders."""
    resolved_token = _resolve_token(app_token, xcmg_app_token, token)
    validation_error = _require(resolved_token, "app_token")
    if validation_error:
        return validation_error

    try:
        records = _client(
            base_url=base_url,
            service_base_url=service_base_url,
        ).fetch_orders(
            app_token=resolved_token,
            vincode=vincode,
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
            "vincode": vincode or None,
            "records": [_compact_record(record) for record in limited_records],
        },
    }


def get_service_order_detail_tool(
    order_id: str,
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """Get one existing service order detail."""
    resolved_token = _resolve_token(app_token, xcmg_app_token, token)
    validation_error = _require(resolved_token, "app_token") or _require(
        order_id,
        "order_id",
    )
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

    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "record": _compact_record(record),
        },
    }
