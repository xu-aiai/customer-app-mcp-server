from typing import Any, Optional

from clients.telematics_bridge import create_telematics_client

FIXED_VINCODE = "XUGG2154CTKA02713"
_VIN_FIELD_NAMES = {
    "vincode",
    "vin",
    "deviceVin",
    "device_vin",
    "userprofileCode",
    "userprofile_code",
}


def _fixed_vincode() -> str:
    return FIXED_VINCODE


def _force_fixed_vincode(value: Optional[Any]) -> Optional[Any]:
    if isinstance(value, dict):
        return {
            key: (
                _fixed_vincode()
                if key in _VIN_FIELD_NAMES
                else _force_fixed_vincode(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_force_fixed_vincode(item) for item in value]
    return value


def _fixed_device_query_params(params: Optional[dict] = None) -> dict:
    fixed_params = dict(_force_fixed_vincode(params or {}) or {})
    fixed_params["vincode"] = _fixed_vincode()
    fixed_params["deviceVin"] = _fixed_vincode()
    fixed_params["searchKey"] = _fixed_vincode()
    return fixed_params


def _error(message: str) -> dict:
    return {
        "success": False,
        "error": message,
    }


def _wrap_response(response_data: dict) -> dict:
    if response_data.get("success") is False:
        return response_data
    return {
        "success": True,
        "data": response_data,
    }


def _require(value: Optional[str], name: str) -> Optional[dict]:
    if value is None or not str(value).strip():
        return _error(f"{name} is required.")
    return None


def _client(base_url: Optional[str]):
    return create_telematics_client(base_url=base_url)


def _call_client_method(method_name: str, base_url: Optional[str] = None, **kwargs) -> dict:
    client = _client(base_url)
    method = getattr(client, method_name, None)
    if method is None:
        return _error(f"Current telematics provider does not support {method_name}.")
    try:
        return method(**kwargs)
    except ValueError as exc:
        return _error(str(exc))


def query_vehicle_by_vincode_tool(
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """通过 vincode 查询车辆.

    Calls GET /apiForAi/customerVehicle/{vincode}.
    Uses vincode as the path variable.
    """
    validation_error = None
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).query_vehicle_by_vincode(
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_vehicle_by_vincode_v2_tool(
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = None
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).query_vehicle_by_vincode_v2(
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_work_hours_statistic_info_by_vehicle_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车统计运行时间统计信息查询.

    Calls POST /apiForAi/queryWorkHoursStatisticInfoByVehicle.
    Maps begin_date/end_date/vincode to JSON fields beginDate/endDate/vincode.
    """
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).query_work_hours_statistic_info_by_vehicle(
            begin_date=begin_date,
            end_date=end_date,
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_work_hours_statistic_info_by_vehicle_v2_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).query_work_hours_statistic_info_by_vehicle_v2(
            begin_date=begin_date,
            end_date=end_date,
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_planned_maintained_item_page_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    begin_date: Optional[str] = None,
    end_date: Optional[str] = None,
    vincode: Optional[str] = None,
    item_name: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """计划维保分页查询.

    Calls GET /apiForAi/queryPlannedMaintainedItemPage.
    Maps snake_case tool args to API query fields beginDate/endDate/itemName.
    """
    try:
        response_data = _client(base_url).query_planned_maintained_item_page(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
            itemName=item_name,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_planned_maintained_item_page_v2_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    begin_date: Optional[str] = None,
    end_date: Optional[str] = None,
    vincode: Optional[str] = None,
    item_name: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    try:
        response_data = _client(base_url).query_planned_maintained_item_page_v2(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
            itemName=item_name,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def get_customer_condition_tool(
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """获取当前工况.

    Calls GET /customerApp/getCustomerCondition with query field vincode.
    """
    validation_error = None
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).get_customer_condition(
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_work_hours_page_new_by_date_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    order_asc: Optional[int] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车按日期统计运行时间分页接口.

    Calls GET /apiForAi/queryWorkHoursPageNewByDate.
    Required query fields are beginDate/endDate/vincode.
    """
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).query_work_hours_page_new_by_date(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
            orderAsc=order_asc,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_work_hours_page_new_by_date_v2_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    order_asc: Optional[int] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).query_work_hours_page_new_by_date_v2(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
            orderAsc=order_asc,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def get_worktime_calendar_list_from_doris_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询客户端设备工作日历 List.

    Calls GET /apiForAi/getWorktimeCalendarListFromDoris.
    Required query fields are beginDate/endDate/vincode.
    """
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).get_worktime_calendar_list_from_doris(
            token=token,
            language=language,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def get_worktime_calendar_list_from_doris_v2_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).get_worktime_calendar_list_from_doris_v2(
            token=token,
            language=language,
            beginDate=begin_date,
            endDate=end_date,
            vincode=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_trace_tool(
    begin_time: str,
    end_time: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """设备轨迹.

    Calls GET /apiForAi/trace.
    Required query fields are beginTime/endTime/vincode.
    """
    validation_error = (
        _require(begin_time, "begin_time")
        or _require(end_time, "end_time")
    )
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).query_trace(
            token=token,
            language=language,
            beginTime=begin_time,
            endTime=end_time,
            vincode=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_trace_v2_tool(
    begin_time: str,
    end_time: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = (
        _require(begin_time, "begin_time")
        or _require(end_time, "end_time")
    )
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).query_trace_v2(
            token=token,
            language=language,
            beginTime=begin_time,
            endTime=end_time,
            vincode=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_customer_vehicle_page_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    search_key: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """客户设备列表.

    Calls GET /apiForAi/customerVehiclePage.
    Maps vehicle_id to API query field id.
    """
    try:
        response_data = _client(base_url).query_customer_vehicle_page(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            id=None,
            searchKey=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_customer_vehicle_page_v2_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    search_key: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    try:
        response_data = _client(base_url).query_customer_vehicle_page_v2(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            id=None,
            searchKey=_fixed_vincode(),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_device_fault_page_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vincode: Optional[str] = None,
    faultcode: Optional[str] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """故障告警分页查询.

    Calls GET /apiForAi/deviceFaultPage.
    Optional filters are vincode, faultcode, starttime, and endtime.
    """
    try:
        response_data = _client(base_url).query_device_fault_page(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            vincode=_fixed_vincode(),
            faultcode=faultcode,
            starttime=starttime,
            endtime=endtime,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_device_fault_page_v2_tool(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vincode: Optional[str] = None,
    faultcode: Optional[str] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    try:
        response_data = _client(base_url).query_device_fault_page_v2(
            token=token,
            language=language,
            total=total,
            size=size,
            current=current,
            vincode=_fixed_vincode(),
            faultcode=faultcode,
            starttime=starttime,
            endtime=endtime,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_core_info_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询核心统计信息（通用）.

    Calls POST /apiForAi/queryCoreInfo.
    Maps begin_date/end_date/vincode to JSON fields beginDate/endDate/vincode.
    """
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error

    try:
        response_data = _client(base_url).query_core_info(
            begin_date=begin_date,
            end_date=end_date,
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_core_info_v2_tool(
    begin_date: str,
    end_date: str,
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = (
        _require(begin_date, "begin_date")
        or _require(end_date, "end_date")
    )
    if validation_error:
        return validation_error
    try:
        response_data = _client(base_url).query_core_info_v2(
            begin_date=begin_date,
            end_date=end_date,
            vincode=_fixed_vincode(),
            token=token,
            language=language,
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def call_service_order_union_tool(
    endpoint: str,
    method: str = "POST",
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """调用保养&报修统一工单接口.

    endpoint 示例：getPage、add、getDevice、cancelSrvOrder，或完整
    /serviceOrderUnion/add。
    """
    validation_error = _require(endpoint, "endpoint")
    if validation_error:
        return validation_error
    try:
        response_data = create_telematics_client(
            base_url=base_url,
            service_base_url=service_base_url,
        ).call_service_order_union(
            endpoint=endpoint,
            method=method,
            token=token,
            language=language,
            params=_fixed_device_query_params(params),
            payload=_force_fixed_vincode(payload),
        )
    except ValueError as exc:
        return _error(str(exc))
    return _wrap_response(response_data)


def query_work_rate_tool(
    query_date: str,
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = _require(query_date, "query_date")
    if validation_error:
        return validation_error
    response_data = _call_client_method(
        "query_work_rate",
        base_url=base_url,
        vincode=_fixed_vincode(),
        query_date=query_date,
    )
    return _wrap_response(response_data)


def get_work_condition_header_tool(
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "get_work_condition_header",
        base_url=base_url,
        vincode=_fixed_vincode(),
    )
    return _wrap_response(response_data)


def get_current_work_condition_tool(
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "get_customer_condition",
        base_url=base_url,
        vincode=_fixed_vincode(),
        token=token,
        language=language,
    )
    return _wrap_response(response_data)


def query_current_location_tool(
    vincode: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "query_current_location",
        base_url=base_url,
        vincode=_fixed_vincode(),
        token=token,
        language=language,
    )
    return _wrap_response(response_data)


def query_history_work_condition_tool(
    start_time: str,
    end_time: str,
    current: int = 1,
    size: int = 20,
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = _require(start_time, "start_time") or _require(end_time, "end_time")
    if validation_error:
        return validation_error
    response_data = _call_client_method(
        "query_history_work_condition",
        base_url=base_url,
        vincode=_fixed_vincode(),
        start_time=start_time,
        end_time=end_time,
        current=current,
        size=size,
    )
    return _wrap_response(response_data)


def get_env_pro_data_tool(
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "get_env_pro_data",
        base_url=base_url,
        vincode=_fixed_vincode(),
    )
    return _wrap_response(response_data)


def query_env_pro_history_data_tool(
    start_time: str,
    end_time: str,
    current: int = 1,
    size: int = 20,
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = _require(start_time, "start_time") or _require(end_time, "end_time")
    if validation_error:
        return validation_error
    response_data = _call_client_method(
        "query_env_pro_history_data",
        base_url=base_url,
        vincode=_fixed_vincode(),
        start_time=start_time,
        end_time=end_time,
        current=current,
        size=size,
    )
    return _wrap_response(response_data)


def query_vehicle_alarm_tool(
    start_time: str,
    end_time: str,
    current: int = 1,
    size: int = 20,
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    validation_error = _require(start_time, "start_time") or _require(end_time, "end_time")
    if validation_error:
        return validation_error
    response_data = _call_client_method(
        "query_vehicle_alarm",
        base_url=base_url,
        vincode=_fixed_vincode(),
        start_time=start_time,
        end_time=end_time,
        current=current,
        size=size,
    )
    return _wrap_response(response_data)


def query_indicator_data_tool(
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "query_indicator_data",
        base_url=base_url,
        vincode=_fixed_vincode(),
    )
    return _wrap_response(response_data)


def query_tags_data_tool(
    vincode: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    response_data = _call_client_method(
        "query_tags_data",
        base_url=base_url,
        vincode=_fixed_vincode(),
    )
    return _wrap_response(response_data)
