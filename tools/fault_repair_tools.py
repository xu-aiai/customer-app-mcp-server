import re
from typing import Any, Dict, List, Optional, Sequence

from clients.crmplus_client import create_repair_order
from clients.telematics_bridge import create_telematics_client
from i18n import t

CustomerAppClient = create_telematics_client

REQUIRED_FIELDS = [
    "vincode",
    "fault_description",
    "new_contact",
    "new_feedbacktel",
]

_ALNUM_VINCODE_RE = re.compile(r"^[A-Za-z0-9]{8,30}$")
FIXED_VINCODE = "XUGG2154CTKA02713"


def _fixed_vincode() -> str:
    return FIXED_VINCODE


def _error(message: str, **extra: Any) -> dict:
    return {
        "success": False,
        "action": extra.pop("action", "ask_missing_info"),
        "error": message,
        "message": message,
        "response": extra.pop("response", message),
        **extra,
    }


def _normalize_submit_error(message: str, language: Optional[str] = None) -> str:
    cleaned = _text(message)
    if cleaned in {"", "-1", "0"}:
        return t("fault_repair.submit_failed_generic", language=language)
    return cleaned


def _ok(action: str, message: str, **extra: Any) -> dict:
    return {
        "success": True,
        "action": action,
        "message": message,
        "response": extra.pop("response", message),
        **extra,
    }


def _text(value: Optional[Any]) -> str:
    return str(value or "").strip()


def _is_english_language(language: Optional[str]) -> bool:
    return str(language or "").lower().startswith("en")


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
    selected_vincode = _resolve_selected_vincode(user_message or "", state.get("devices"))
    if selected_vincode:
        state["vincode"] = selected_vincode
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

    vin_match = re.search(
        r"(?:整机编码|车架号|VIN|vin|设备编码|device\s*vin|device\s*code|chassis\s*number)[:：\s]*([A-Za-z0-9_-]{5,})",
        message,
        re.IGNORECASE,
    )
    if vin_match:
        result["vincode"] = vin_match.group(1)

    contact_match = re.search(
        r"(?:联系人|现场联系人|姓名|contact|contact\s*person|name)[:：\s]*([\u4e00-\u9fa5A-Za-z]{2,24})",
        message,
        re.IGNORECASE,
    )
    if contact_match:
        result["new_contact"] = contact_match.group(1)

    fault_match = re.search(
        r"(?:故障|问题|现象|报修内容|故障描述|fault|issue|problem|symptom|fault description)[:：\s]*(.{2,160})",
        message,
        re.IGNORECASE,
    )
    if fault_match:
        result["fault_description"] = _clean_fault_description(fault_match.group(1))
    else:
        inferred_fault = _infer_fault_description(message)
        if inferred_fault:
            result["fault_description"] = inferred_fault
    return result


def _clean_fault_description(value: str) -> str:
    cleaned = _text(value)
    cleaned = re.split(
        r"(?:[;；\n]+|\b(?:contact|contact person|name|phone|tel|mobile|联系人|现场联系人|姓名|电话|手机号)[:：])",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return cleaned.strip(" ，,。；;：:")


def _infer_fault_description(message: str) -> str:
    cleaned = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "", message)
    cleaned = re.sub(
        r"(?:整机编码|车架号|VIN|vin|设备编码|device\s*vin|device\s*code|chassis\s*number)[:：\s]*[A-Za-z0-9_-]{5,}",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:联系人|现场联系人|姓名|contact|contact\s*person|name)[:：\s]*[\u4e00-\u9fa5A-Za-z]{2,24}",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"第\s*(?:一|二|三|1|2|3)\s*(?:台|辆|个|条|号)?", "", cleaned)
    cleaned = re.sub(r"(?:一|二|三|1|2|3)\s*(?:台|辆|个|条|号)", "", cleaned)
    cleaned = re.sub(r"\b(?:first|second|third|1st|2nd|3rd)\b", "", cleaned, flags=re.IGNORECASE)
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
        "broken",
        "fail",
        "failure",
        "fault",
        "issue",
        "problem",
        "alarm",
        "error",
        "cannot",
        "can't",
        "won't",
        "not working",
        "no power",
        "no response",
        "won't start",
        "can't start",
        "leak",
        "noise",
    )
    for fragment in fragments:
        if 2 <= len(fragment) <= 80 and any(keyword in fragment for keyword in fault_keywords):
            return fragment
    return ""


def _resolve_selected_vincode(message: str, devices: Optional[Any]) -> str:
    if not isinstance(devices, list) or not devices:
        return ""
    text = _text(message)
    if not text:
        return ""

    selected_index = _parse_device_index(text, len(devices))
    if selected_index is not None:
        device = devices[selected_index]
        if isinstance(device, dict):
            return _device_vincode(device)

    return _match_device_from_text(text, devices)


def _parse_device_index(message: str, device_count: int) -> Optional[int]:
    text = message.strip()
    if not text:
        return None

    if device_count == 1 and re.search(r"这台|那台|这个|那个|它|this one|that one|it", text, re.IGNORECASE):
        return 0

    patterns = [
        r"第\s*(?P<num>[0-9]{1,2}|[零一二三四五六七八九十两]+)\s*(?:台|辆|个|条|号|辆车|台车|个车)?",
        r"(?<!\d)(?P<num>[0-9]{1,2}|[零一二三四五六七八九十两]+)\s*(?:台|辆|个|条|号|辆车|台车|个车)(?!\w)",
        r"\b(?P<num>[0-9]{1,2})(?:st|nd|rd|th)\b",
        r"\b(?P<num>first|second|third)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        index = _parse_ordinal_number(match.group("num"))
        if index is None:
            continue
        zero_based = index - 1
        if 0 <= zero_based < device_count:
            return zero_based
    return None


def _parse_ordinal_number(value: str) -> Optional[int]:
    cleaned = _text(value)
    if not cleaned:
        return None
    lower = cleaned.lower()
    english_numerals = {
        "first": 1,
        "second": 2,
        "third": 3,
    }
    if lower in english_numerals:
        return english_numerals[lower]
    if lower.endswith(("st", "nd", "rd", "th")) and lower[:-2].isdigit():
        return int(lower[:-2])
    if cleaned.isdigit():
        return int(cleaned)
    numerals = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    if cleaned == "十":
        return 10
    if len(cleaned) == 1:
        return numerals.get(cleaned)
    if cleaned.startswith("十"):
        tail = numerals.get(cleaned[1:])
        return 10 + (tail or 0) if tail is not None else 10
    if cleaned.endswith("十") and len(cleaned) == 2:
        head = numerals.get(cleaned[0])
        return (head or 1) * 10 if head is not None else None
    if "十" in cleaned:
        head, tail = cleaned.split("十", 1)
        head_value = numerals.get(head) if head else 1
        tail_value = numerals.get(tail) if tail else 0
        if head_value is None or tail_value is None:
            return None
        return head_value * 10 + tail_value
    return None


def _normalize_alnum(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", _text(value)).upper()


def _device_vincode(device: dict) -> str:
    return _text(
        device.get("vincode")
        or device.get("deviceVin")
        or device.get("VIN")
        or device.get("vin")
    )


def _device_search_text(device: dict) -> str:
    parts = [
        _device_vincode(device),
        _text(device.get("deviceId") or device.get("id") or device.get("vehicleId")),
        _text(device.get("deviceName")),
        _text(device.get("deviceModel")),
    ]
    return " ".join(part for part in parts if part)


def _match_device_from_text(message: str, devices: Sequence[dict]) -> str:
    text = _text(message)
    if not text:
        return ""

    normalized_text = _normalize_alnum(text)
    if len(normalized_text) < 5 and not re.search(r"[\u4e00-\u9fa5]", text):
        return ""

    if len(normalized_text) >= 5:
        for device in devices:
            if not isinstance(device, dict):
                continue
            vincode = _device_vincode(device)
            if not vincode:
                continue
            normalized_vincode = _normalize_alnum(vincode)
            if normalized_vincode and (
                normalized_text == normalized_vincode
                or normalized_text in normalized_vincode
                or normalized_vincode in normalized_text
            ):
                return vincode

    if re.search(r"[\u4e00-\u9fa5]", text):
        for device in devices:
            if not isinstance(device, dict):
                continue
            search_text = _device_search_text(device)
            if search_text and text == search_text:
                return _device_vincode(device)
            if search_text and text in search_text:
                return _device_vincode(device)
    return ""


def _is_probable_vincode(value: str) -> bool:
    return bool(_ALNUM_VINCODE_RE.fullmatch(_normalize_alnum(value)))


def _missing_fields(state: dict) -> List[str]:
    return [field for field in REQUIRED_FIELDS if not state.get(field)]


def _join_labels(values: Sequence[str], language: Optional[str] = None) -> str:
    separator = ", " if str(language or "").lower().startswith("en") else "、"
    return separator.join(values)


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


def _enrich_devices(devices: List[dict], language: Optional[str] = None) -> List[dict]:
    enriched: List[dict] = []
    for index, device in enumerate(devices, start=1):
        item = dict(device)
        item["index"] = index
        item["label"] = f"Device #{index}" if _is_english_language(language) else f"第{index}辆"
        enriched.append(item)
    return enriched


def _validate_or_resolve_vincode(
    state: dict,
    language: Optional[str] = None,
) -> tuple[str, Optional[dict]]:
    vincode = _text(state.get("vincode"))
    devices = state.get("devices")
    if not vincode:
        return "", None
    if isinstance(devices, list) and devices:
        matched = _match_device_from_text(vincode, devices)
        if matched:
            return matched, None
        if re.search(r"[\u4e00-\u9fa5]", vincode) or not _is_probable_vincode(vincode):
            return "", {
                "action": "ask_missing_info",
                "message": t("fault_repair.device_not_found", language=language),
            }
        return "", {
            "action": "ask_missing_info",
            "message": t("fault_repair.device_not_found", language=language),
        }
    if not _is_probable_vincode(vincode):
        return "", {
            "action": "ask_missing_info",
            "message": t("fault_repair.invalid_vincode", language=language),
        }
    return vincode, None


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
        "value": t("fault_repair.confirm_value", language=state.get("language")),
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
    state["language"] = language
    state["vincode"] = _fixed_vincode()
    state.pop("devices", None)

    try:
        client = CustomerAppClient(base_url=base_url)
    except Exception:
        return _error(t("fault_repair.init_failed", language=language), state=state)

    resolved_vincode, validation_error = _validate_or_resolve_vincode(state, language=language)
    if validation_error:
        state["vincode"] = ""
        return _error(
            validation_error["message"],
            action=validation_error["action"],
            state=state,
        )
    if resolved_vincode:
        state["vincode"] = resolved_vincode

    if not state["vincode"]:
        return _error(t("fault_repair.fixed_vincode_missing", language=language), state=state)

    try:
        detail_result = client.query_vehicle_by_vincode(
            vincode=state["vincode"],
            token=resolved_token,
            language=language,
        )
    except ValueError:
        return _error(t("fault_repair.fixed_vincode_invalid", language=language), state=state)
    if _api_failed(detail_result):
        return _error(
            t("fault_repair.device_not_found", language=language),
            state=state,
        )

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
            "fault_description": t("fault_repair.field.fault_description", language=language),
            "new_contact": t("fault_repair.field.new_contact", language=language),
            "new_feedbacktel": t("fault_repair.field.new_feedbacktel", language=language),
            "vincode": t("fault_repair.field.vincode", language=language),
        }
        return _ok(
            "ask_missing_info",
            t(
                "fault_repair.missing_fields_prefix",
                language=language,
                fields=_join_labels([labels[field] for field in missing], language=language),
            ),
            missing_fields=missing,
            state=state,
        )

    payload = _build_submit_payload(state, profile)
    return _ok(
        "confirm_submit",
        t("fault_repair.confirm_submit", language=language),
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
    language: Optional[str] = None,
) -> dict:
    """Create the CRM+ repair order after the submitWorkorder payload is confirmed."""
    payload = dict(payload or {})
    resolved_device_vin = _fixed_vincode()
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
        return _error(
            t(
                "common.missing_required_fields",
                language=language,
                fields=", ".join(missing),
            )
        )

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
        message = _normalize_submit_error(str(exc), language=language)
        return _error(message, action="submit_failed", response=message)

    return {
        "success": True,
        "message": t("fault_repair.submit_success", language=language),
        "data": result,
    }
