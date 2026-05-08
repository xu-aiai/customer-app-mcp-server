import re
from typing import Any, Dict, List, Optional, Sequence

from clients.crmplus_client import create_repair_order
from clients.customer_app import CustomerAppClient


REQUIRED_FIELDS = [
    "vincode",
    "fault_description",
    "new_contact",
    "new_feedbacktel",
]


def _error(message: str, **extra: Any) -> dict:
    return {
        "success": False,
        "error": message,
        **extra,
    }


def _ok(action: str, message: str, **extra: Any) -> dict:
    return {
        "success": True,
        "action": action,
        "message": message,
        **extra,
    }


def _text(value: Optional[Any]) -> str:
    return str(value or "").strip()


def _merge_state(
    session_state: Optional[dict],
    user_message: Optional[str],
    conversation_history: Optional[Sequence[Any]],
    vincode: Optional[str],
    fault_description: Optional[str],
    new_contact: Optional[str],
    new_feedbacktel: Optional[str],
) -> dict:
    state = dict(session_state or {})
    parsed = _parse_message(_conversation_text(conversation_history, user_message))
    for key, value in parsed.items():
        if value:
            state[key] = value
    selected_vincode = _resolve_selected_vincode(user_message or "", state.get("devices"))
    if selected_vincode:
        state["vincode"] = selected_vincode
    explicit = {
        "vincode": vincode,
        "fault_description": fault_description,
        "new_contact": new_contact,
        "new_feedbacktel": new_feedbacktel,
    }
    for key, value in explicit.items():
        value = _text(value)
        if value:
            state[key] = value
    for key in REQUIRED_FIELDS:
        state[key] = _text(state.get(key))
    return state


def _conversation_text(
    conversation_history: Optional[Sequence[Any]],
    user_message: Optional[str],
) -> str:
    parts: List[str] = []
    for item in list(conversation_history or [])[-10:]:
        if isinstance(item, str):
            parts.append(item)
            continue
        if isinstance(item, dict):
            role = item.get("role") or item.get("type") or ""
            content = item.get("content") or item.get("message") or item.get("text") or ""
            if content:
                parts.append(f"{role}: {content}" if role else str(content))
    if user_message:
        parts.append(str(user_message))
    return "\n".join(parts)


def _parse_message(message: str) -> dict:
    """Lightweight fallback parser; callers should pass extracted fields when possible."""
    result: Dict[str, str] = {}
    phone_match = re.search(r"(?<!\d)(1[3-9]\d{9})(?!\d)", message)
    if phone_match:
        result["new_feedbacktel"] = phone_match.group(1)

    vin_match = re.search(r"(?:整机编码|车架号|VIN|vin|设备编码)[:：\s]*([A-Za-z0-9_-]{5,})", message)
    if vin_match:
        result["vincode"] = vin_match.group(1)

    contact_match = re.search(r"(?:联系人|现场联系人|姓名)[:：\s]*([\u4e00-\u9fa5A-Za-z]{2,12})", message)
    if contact_match:
        result["new_contact"] = contact_match.group(1)

    fault_match = re.search(r"(?:故障|问题|现象|报修内容|故障描述)[:：\s]*(.{2,120})", message)
    if fault_match:
        result["fault_description"] = fault_match.group(1).strip()
    else:
        inferred_fault = _infer_fault_description(message)
        if inferred_fault:
            result["fault_description"] = inferred_fault
    return result


def _infer_fault_description(message: str) -> str:
    cleaned = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "", message)
    cleaned = re.sub(r"(?:整机编码|车架号|VIN|vin|设备编码)[:：\s]*[A-Za-z0-9_-]{5,}", "", cleaned)
    cleaned = re.sub(r"(?:联系人|现场联系人|姓名)[:：\s]*[\u4e00-\u9fa5A-Za-z]{2,12}", "", cleaned)
    cleaned = re.sub(r"第\s*(?:一|二|三|1|2|3)\s*(?:台|辆|个|条|号)?", "", cleaned)
    cleaned = re.sub(r"(?:一|二|三|1|2|3)\s*(?:台|辆|个|条|号)", "", cleaned)
    fragments = [
        fragment.strip(" ，,。；;：:")
        for fragment in re.split(r"[\n，,。；;]", cleaned)
        if fragment.strip(" ，,。；;：:")
    ]
    fault_keywords = (
        "坏",
        "故障",
        "报警",
        "报错",
        "漏",
        "异响",
        "无电",
        "无法",
        "不能",
        "不动",
        "启动",
        "熄火",
        "高温",
        "没劲",
        "无力",
    )
    for fragment in fragments:
        if 2 <= len(fragment) <= 80 and any(keyword in fragment for keyword in fault_keywords):
            return fragment
    return ""


def _resolve_selected_vincode(message: str, devices: Optional[Any]) -> str:
    if not isinstance(devices, list) or not devices:
        return ""
    text = message.strip()
    if not text:
        return ""

    selected_index: Optional[int] = None
    ordinal_patterns = [
        (r"第\s*(一|1)|(?:一|1)\s*(?:台|辆|个|条|号)", 0),
        (r"第\s*(二|2)|(?:二|2)\s*(?:台|辆|个|条|号)", 1),
        (r"第\s*(三|3)|(?:三|3)\s*(?:台|辆|个|条|号)", 2),
    ]
    for pattern, index in ordinal_patterns:
        if re.search(pattern, text):
            selected_index = index
            break
    if selected_index is None and re.search(r"这台|那台|这个|那个", text):
        selected_index = 0 if len(devices) == 1 else None
    if selected_index is None or selected_index >= len(devices):
        return ""

    device = devices[selected_index]
    if not isinstance(device, dict):
        return ""
    return _text(
        device.get("vincode")
        or device.get("deviceVin")
        or device.get("VIN")
        or device.get("vin")
    )


def _missing_fields(state: dict) -> List[str]:
    return [field for field in REQUIRED_FIELDS if not state.get(field)]


def _pick_vehicle_profile(detail_result: dict) -> dict:
    """Pick vehicle profile from old and new customer-app detail response shapes."""
    if not isinstance(detail_result, dict):
        return {}

    if isinstance(detail_result.get("data"), dict) and not isinstance(
        detail_result.get("sections"), dict
    ):
        return detail_result.get("data") or {}

    sections = detail_result.get("sections")
    if not isinstance(sections, dict):
        return {}
    vehicle_profile = sections.get("vehicleProfile")
    if not isinstance(vehicle_profile, dict):
        return {}
    profile_resp = vehicle_profile.get("data")
    if not isinstance(profile_resp, dict):
        return {}
    payload = profile_resp.get("data")
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        kv_style = all(
            isinstance(item, dict) and "key" in item
            for item in payload
            if isinstance(item, dict)
        )
        if kv_style:
            out = {}
            for item in payload:
                key = _text(item.get("key"))
                if key:
                    out[key] = item.get("value")
            return out
        for row in payload:
            if isinstance(row, dict):
                return row
    return {}


def _extract_devices(response_data: dict) -> List[dict]:
    data = response_data.get("data") if isinstance(response_data, dict) else {}
    if isinstance(data, dict):
        devices = data.get("items") or data.get("records") or data.get("list") or []
    elif isinstance(data, list):
        devices = data
    else:
        devices = []
    return [item for item in devices if isinstance(item, dict)]


def _api_failed(response_data: dict) -> bool:
    if not isinstance(response_data, dict):
        return True
    if response_data.get("success") is False:
        return True
    code = response_data.get("code")
    return code is not None and code != 0


def _device_summary(device: dict) -> dict:
    return {
        "vincode": device.get("vincode") or device.get("VIN") or device.get("vin") or "",
        "deviceId": device.get("id") or device.get("vehicleId") or device.get("deviceId") or "",
        "deviceName": (
            device.get("productTypeName")
            or device.get("vehicleName")
            or device.get("deviceName")
            or ""
        ),
        "deviceModel": device.get("modelTypeName") or device.get("modelTypeCode") or "",
    }


def _build_submit_payload(state: dict, profile: dict) -> dict:
    model_type = profile.get("modelType")
    product_type = profile.get("productType")
    device_id = profile.get("id") or profile.get("vehicleId") or profile.get("deviceId") or ""
    detail_address = (
        profile.get("address")
        or profile.get("cacheAddr")
        or profile.get("cache_addr")
        or profile.get("detailAddress")
        or profile.get("location")
        or ""
    )
    device_model = (
        (model_type.get("name") if isinstance(model_type, dict) else "")
        or profile.get("modelTypeName")
        or profile.get("modelTypeCode")
        or ""
    )
    device_name = (
        (product_type.get("name") if isinstance(product_type, dict) else "")
        or profile.get("productTypeName")
        or profile.get("vehicleName")
        or profile.get("deviceName")
        or ""
    )
    return {
        "value": "确认",
        "action": "confirm_work_order",
        "type": "submitWorkorder",
        "deviceVin": state["vincode"],
        "faultDescription": state["fault_description"],
        "deviceId": device_id,
        "deviceModel": device_model,
        "detailAddress": detail_address,
        "deviceName": device_name,
        "contactName": state["new_contact"],
        "contactPhone": state["new_feedbacktel"],
    }


def prepare_fault_repair_tool(
    user_message: Optional[str] = None,
    conversation_history: Optional[Sequence[Any]] = None,
    session_state: Optional[dict] = None,
    vincode: Optional[str] = None,
    fault_description: Optional[str] = None,
    new_contact: Optional[str] = None,
    new_feedbacktel: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    platform_type: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """Prepare fault repair parameters without creating a CRM work order."""
    del platform_type
    resolved_token = token or xcmg_app_token
    state = _merge_state(
        session_state=session_state,
        user_message=user_message,
        conversation_history=conversation_history,
        vincode=vincode,
        fault_description=fault_description,
        new_contact=new_contact,
        new_feedbacktel=new_feedbacktel,
    )

    try:
        client = CustomerAppClient(base_url=base_url)
    except Exception as exc:
        return _error(str(exc), state=state)

    if not state["vincode"]:
        try:
            response_data = client.query_customer_vehicle_page(
                token=resolved_token,
                language=language,
                current=1,
                size=20,
            )
        except ValueError as exc:
            return _error(str(exc), state=state)
        if _api_failed(response_data):
            return _error("获取设备列表失败。", detail=response_data, state=state)

        devices = [_device_summary(device) for device in _extract_devices(response_data)]
        devices = [device for device in devices if device.get("vincode")]
        state["devices"] = devices
        if not devices:
            return _ok("no_device", "您当前暂无绑定设备，无法进行故障报修。", state=state)
        return _ok(
            "select_device",
            "请选择需要故障报修的设备。",
            devices=devices,
            state=state,
        )

    try:
        detail_result = client.query_vehicle_by_vincode(
            vincode=state["vincode"],
            token=resolved_token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc), state=state)
    if _api_failed(detail_result):
        return _error("获取设备详情失败，无法进行故障报修。", detail=detail_result, state=state)

    profile = _pick_vehicle_profile(detail_result)
    state.update(
        {
            "device_id": profile.get("id")
            or profile.get("vehicleId")
            or profile.get("deviceId")
            or "",
            "device_model": (
                profile.get("modelType", {}).get("name")
                if isinstance(profile.get("modelType"), dict)
                else ""
            )
            or profile.get("modelTypeName")
            or profile.get("modelTypeCode")
            or "",
            "device_name": (
                profile.get("productType", {}).get("name")
                if isinstance(profile.get("productType"), dict)
                else ""
            )
            or profile.get("productTypeName")
            or profile.get("vehicleName")
            or profile.get("deviceName")
            or "",
            "detail_address": profile.get("address")
            or profile.get("cacheAddr")
            or profile.get("cache_addr")
            or profile.get("detailAddress")
            or profile.get("location")
            or "",
        }
    )

    missing = _missing_fields(state)
    if missing:
        labels = {
            "fault_description": "故障描述",
            "new_contact": "现场联系人姓名",
            "new_feedbacktel": "现场联系人电话",
            "vincode": "整机编码",
        }
        return _ok(
            "ask_missing_info",
            "请补充：" + "、".join(labels[field] for field in missing),
            missing_fields=missing,
            state=state,
        )

    payload = _build_submit_payload(state, profile)
    return _ok(
        "confirm_submit",
        "请确认报修信息并提交工单。",
        submit_payload=payload,
        state=state,
    )


def submit_fault_repair_order_tool(
    payload: Optional[dict] = None,
    device_vin: Optional[str] = None,
    fault_description: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_phone: Optional[str] = None,
    detail_address: Optional[str] = None,
    source: int = 7,
) -> dict:
    """Create the CRM+ repair order after the submitWorkorder payload is confirmed."""
    payload = dict(payload or {})
    resolved_device_vin = _text(device_vin or payload.get("deviceVin"))
    resolved_fault_description = _text(
        fault_description or payload.get("faultDescription")
    )
    resolved_contact_name = _text(contact_name or payload.get("contactName"))
    resolved_contact_phone = _text(contact_phone or payload.get("contactPhone"))
    resolved_detail_address = _text(detail_address or payload.get("detailAddress"))

    missing = [
        name
        for name, value in {
            "device_vin": resolved_device_vin,
            "fault_description": resolved_fault_description,
            "contact_name": resolved_contact_name,
            "contact_phone": resolved_contact_phone,
        }.items()
        if not value
    ]
    if missing:
        return _error("Missing required fields: " + ", ".join(missing))

    try:
        result = create_repair_order(
            contact=resolved_contact_name,
            feedback_tel=resolved_contact_phone,
            userprofile_code=resolved_device_vin,
            memo=resolved_fault_description,
            address=resolved_detail_address,
            source=source,
        )
    except Exception as exc:
        return _error(str(exc))

    return {
        "success": True,
        "message": "维修服务单创建成功。",
        "data": result,
    }
