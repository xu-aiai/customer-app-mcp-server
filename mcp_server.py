# server.py
from fastmcp import FastMCP
import sys
import logging
from typing import Optional
from tools.customer_app_tools import (
    call_service_order_union_tool,
    get_customer_condition_tool,
    get_worktime_calendar_list_from_doris_tool,
    get_worktime_calendar_list_from_doris_v2_tool,
    query_core_info_tool,
    query_core_info_v2_tool,
    query_customer_vehicle_page_tool,
    query_customer_vehicle_page_v2_tool,
    query_device_fault_page_tool,
    query_device_fault_page_v2_tool,
    query_planned_maintained_item_page_tool,
    query_planned_maintained_item_page_v2_tool,
    query_trace_tool,
    query_trace_v2_tool,
    query_vehicle_by_vincode_tool,
    query_vehicle_by_vincode_v2_tool,
    query_work_hours_page_new_by_date_tool,
    query_work_hours_page_new_by_date_v2_tool,
    query_work_hours_statistic_info_by_vehicle_tool,
    query_work_hours_statistic_info_by_vehicle_v2_tool,
)
from tools.calculator_tools import calculate_expression
from tools.fault_repair_tools import (
    prepare_fault_repair_tool,
    submit_fault_repair_order_tool,
)
from tools.service_order_tools import (
    get_service_order_detail_tool,
    list_service_orders_tool,
)
from clients.customer_app_auth import fetch_customer_app_token
from clients.customer_app_config import load_customer_app_config

logger = logging.getLogger('MCPServer')

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# Create an MCP server
mcp = FastMCP("CustomerAppMCP")


def refresh_customer_app_token_on_startup() -> None:
    """Fetch customer app token on server startup and persist it to config."""
    try:
        config = load_customer_app_config()
        auth_config = config.get("auth") or {}
        required_values = [
            config.get("auth_base_url"),
            auth_config.get("authorization"),
            auth_config.get("username"),
            auth_config.get("password"),
        ]
        if not all(required_values):
            logger.info("Skip customer app token refresh: auth config is incomplete.")
            return
        fetch_customer_app_token()
    except Exception as exc:
        logger.warning("Failed to refresh customer app token on startup: %s", exc)

# Add an addition tool
@mcp.tool()
def calculator(python_expression: str) -> dict:
    """数学表达式计算工具，用于精确计算 Python 数学表达式。

    适用问题：
    - 计算加减乘除、幂运算、取整、随机数等数学结果。
    - 需要使用 math 或 random 模块完成计算。

    参数：
    - python_expression: Python 表达式字符串，可直接使用 math 和 random，不需要 import。
    """
    return calculate_expression(python_expression)


@mcp.tool()
def query_vehicle_by_vincode(
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """通过 vincode 查询车辆详情，用于按设备编码/车架号获取单台车辆基础信息。

    适用问题：
    - 查询某个 VIN/车架号/设备编码对应的车辆信息。
    - 查看单台设备的终端号、车型、设备类型、实时定位概览等基础资料。

    API: GET /apiForAi/customerVehicle/{vincode}
    必填参数：
    - vincode: 设备编码/车架号。
    """
    return query_vehicle_by_vincode_tool(
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_work_hours_statistic_info_by_vehicle(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车统计运行时间汇总信息，用于查询某台设备在日期范围内的工时统计总览。

    适用问题：
    - 统计某台车一段时间内的运行时间、工作时间、怠速时间。
    - 查看某台设备在开始日期到结束日期之间的工时汇总。

    API: POST /apiForAi/queryWorkHoursStatisticInfoByVehicle
    必填参数：
    - begin_date: 开始日期，格式 yyyy-MM-dd。
    - end_date: 结束日期，格式 yyyy-MM-dd。
    - vincode: 设备编码/车架号。
    """
    return query_work_hours_statistic_info_by_vehicle_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_planned_maintained_item_page(
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
    """计划维保分页查询，用于查询车辆/设备的计划保养、计划维护提醒列表。

    适用问题：
    - 查询某台车的计划维保记录。
    - 按提醒日期范围、车架号、计划名称筛选维保计划。
    - 分页查看计划维护项目。

    API: GET /apiForAi/queryPlannedMaintainedItemPage
    可选参数：
    - current/size/total: 分页参数。
    - begin_date/end_date: 提醒开始/结束日期，格式 yyyy-MM-dd。
    - vincode: 车架号。
    - item_name: 计划名称模糊搜索条件。
    """
    return query_planned_maintained_item_page_tool(
        total=total,
        size=size,
        current=current,
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        item_name=item_name,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def get_customer_condition(
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """获取当前工况，用于查询某台车辆/设备的当前实时工况状态。

    适用问题：
    - 查看某台设备当前工况。
    - 查询车辆当前运行状态、在线状态或实时作业状态。

    API: GET /customerApp/getCustomerCondition
    必填参数：
    - vincode: 车架号/设备编码。
    """
    return get_customer_condition_tool(
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_work_hours_page_new_by_date(
    begin_date: str,
    end_date: str,
    vincode: str,
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    order_asc: Optional[int] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车按日期分页查询运行时间明细，用于查看某台设备每天的工时明细。

    适用问题：
    - 查询某台车每天的运行时间、工作时间、怠速时间明细。
    - 按日期分页查看设备工时记录。
    - 需要明细列表时使用本工具；只要汇总时使用 query_work_hours_statistic_info_by_vehicle。

    API: GET /apiForAi/queryWorkHoursPageNewByDate
    必填参数：
    - begin_date: 开始日期，格式 yyyy-MM-dd。
    - end_date: 结束日期，格式 yyyy-MM-dd。
    - vincode: 设备编码。
    可选参数：
    - current/size/total: 分页参数。
    - order_asc: 排序顺序，1 表示时间正序，默认倒序。
    """
    return query_work_hours_page_new_by_date_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        total=total,
        size=size,
        current=current,
        order_asc=order_asc,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def get_worktime_calendar_list_from_doris(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询客户端设备工作日历列表，用于查看某台设备在日期范围内的工作日历。

    适用问题：
    - 查询设备某段时间的工作日历。
    - 查看某台车哪些日期有工作记录。
    - 按日期正序获取工作日历列表。

    API: GET /apiForAi/getWorktimeCalendarListFromDoris
    必填参数：
    - begin_date: 开始日期，格式 yyyy-MM-dd。
    - end_date: 结束日期，格式 yyyy-MM-dd。
    - vincode: 设备编码。
    """
    return get_worktime_calendar_list_from_doris_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_trace(
    begin_time: str,
    end_time: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """设备轨迹查询，用于查询某台设备在指定时间段内的历史定位轨迹点。

    适用问题：
    - 查询车辆/设备轨迹。
    - 查看某台车在某段时间的行驶路线、历史定位点。
    - 获取设备从开始时间到结束时间的轨迹数据。

    API: GET /apiForAi/trace
    必填参数：
    - begin_time: 开始时间，格式 yyyy-MM-dd HH:mm:ss。
    - end_time: 结束时间，格式 yyyy-MM-dd HH:mm:ss。
    - vincode: 设备编码。
    """
    return query_trace_tool(
        begin_time=begin_time,
        end_time=end_time,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_customer_vehicle_page(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    search_key: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """客户设备列表分页查询，用于查询客户名下车辆/设备列表。

    适用问题：
    - 查询客户设备列表。
    - 按设备名称或设备编码搜索车辆。
    - 分页查看车辆/设备基础列表。

    API: GET /apiForAi/customerVehiclePage
    可选参数：
    - current/size/total: 分页参数。
    - vehicle_id: 车辆 id，对应接口参数 id。
    - search_key: 设备名称/设备编码搜索关键字。
    """
    return query_customer_vehicle_page_tool(
        total=total,
        size=size,
        current=current,
        vehicle_id=vehicle_id,
        search_key=search_key,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_device_fault_page(
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
    """故障告警分页查询，用于查询设备故障码、故障告警记录列表。

    适用问题：
    - 查询某台设备的故障告警。
    - 按故障代码筛选告警记录。
    - 按开始时间和结束时间分页查看故障列表。

    API: GET /apiForAi/deviceFaultPage
    可选参数：
    - current/size/total: 分页参数。
    - vincode: 设备编码。
    - faultcode: 故障代码。
    - starttime/endtime: 开始/结束时间。
    """
    return query_device_fault_page_tool(
        total=total,
        size=size,
        current=current,
        vincode=vincode,
        faultcode=faultcode,
        starttime=starttime,
        endtime=endtime,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_core_info(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询核心统计信息（通用），用于获取某台设备在日期范围内的核心指标汇总。

    适用问题：
    - 查询车辆核心统计指标。
    - 获取某台设备一段时间内的关键经营/运行统计。
    - 需要通用核心汇总信息时使用本工具。

    API: POST /apiForAi/queryCoreInfo
    必填参数：
    - begin_date: 开始日期，格式 yyyy-MM-dd。
    - end_date: 结束日期，格式 yyyy-MM-dd。
    - vincode: 设备编码/车架号。
    """
    return query_core_info_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def prepare_fault_repair(
    user_message: Optional[str] = None,
    conversation_history: Optional[list] = None,
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
    """准备故障报修信息，不直接创建 CRM 工单。

    适用问题：
    - 用户要新报修，需要抽取/补齐整机编码、故障描述、现场联系人和电话。
    - 没有整机编码时，返回用户绑定设备列表供选择。
    - 信息齐全时，返回 submitWorkorder payload 供确认提交。

    必填信息：
    - vincode/deviceVin: 整机编码。
    - fault_description/faultDescription: 故障描述。
    - new_contact/contactName: 现场联系人姓名。
    - new_feedbacktel/contactPhone: 现场联系人电话。

    注意：本工具只生成待提交参数，不会调用 CRM+ 创建工单。
    """
    return prepare_fault_repair_tool(
        user_message=user_message,
        conversation_history=conversation_history,
        session_state=session_state,
        vincode=vincode,
        fault_description=fault_description,
        new_contact=new_contact,
        new_feedbacktel=new_feedbacktel,
        xcmg_app_token=xcmg_app_token,
        platform_type=platform_type,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def submit_fault_repair_order(
    payload: Optional[dict] = None,
    device_vin: Optional[str] = None,
    fault_description: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_phone: Optional[str] = None,
    detail_address: Optional[str] = None,
    source: int = 7,
) -> dict:
    """确认后创建 CRM+ 维修服务单。

    适用问题：
    - 用户已确认 prepare_fault_repair 返回的 submitWorkorder payload。
    - 需要真正调用 CRM+ /api/service/CreateWorkOrder 创建维修工单。

    可直接传入 prepare_fault_repair 的 submit_payload，也可传入拆分字段。
    CRM+ 配置来自 config/customer_app_config.json 的 crmplus_base_url、
    crmplus_app_id、crmplus_app_secret。
    """
    return submit_fault_repair_order_tool(
        payload=payload,
        device_vin=device_vin,
        fault_description=fault_description,
        contact_name=contact_name,
        contact_phone=contact_phone,
        detail_address=detail_address,
        source=source,
    )


@mcp.tool()
def list_service_orders(
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
    """查询当前用户已有工单/服务单列表，默认返回最近 3 条。

    适用问题：
    - 我的工单到哪了。
    - 服务单进度。
    - 上次报修怎么样了。
    - 最近的报修。
    - 我提的工单状态。

    API: GET /ixcmg/serviceOrderUnion/getPage
    必填参数：
    - app_token/xcmg_app_token: 客户 App 用户 token。
    可选参数：
    - vincode: 设备 VIN，存在时按设备过滤。
    - page_num/page_size: 分页参数，默认 1/3。

    返回压缩后的结构化 records，不做 LLM 总结。
    """
    return list_service_orders_tool(
        app_token=app_token,
        xcmg_app_token=xcmg_app_token,
        vincode=vincode,
        page_num=page_num,
        page_size=page_size,
        token=token,
        language=language,
        base_url=base_url,
        service_base_url=service_base_url,
    )


@mcp.tool()
def get_service_order_detail(
    order_id: str,
    app_token: Optional[str] = None,
    xcmg_app_token: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """查询单条已有工单/服务单详情。

    适用问题：
    - 查工单 12345 的详情。
    - 那条工单的具体情况。
    - 查 CRM123456 的详情。

    API: GET /ixcmg/serviceOrderUnion/{order_id}
    必填参数：
    - order_id: 工单 ID、CRM 编号或服务单编号。
    - app_token/xcmg_app_token: 客户 App 用户 token。

    返回压缩后的结构化 record，不做 LLM 总结。
    """
    return get_service_order_detail_tool(
        order_id=order_id,
        app_token=app_token,
        xcmg_app_token=xcmg_app_token,
        token=token,
        language=language,
        base_url=base_url,
        service_base_url=service_base_url,
    )


@mcp.tool()
def query_vehicle_by_vincode_v2(
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """通过 vincode 查询车辆详情 v2。API: GET /apiForAi/v2/customerVehicle/{vincode}。"""
    return query_vehicle_by_vincode_v2_tool(
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_work_hours_statistic_info_by_vehicle_v2(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车统计运行时间汇总信息 v2。API: POST /apiForAi/v2/queryWorkHoursStatisticInfoByVehicle。"""
    return query_work_hours_statistic_info_by_vehicle_v2_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_planned_maintained_item_page_v2(
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
    """计划维保分页查询 v2。API: GET /apiForAi/v2/queryPlannedMaintainedItemPage。"""
    return query_planned_maintained_item_page_v2_tool(
        total=total,
        size=size,
        current=current,
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        item_name=item_name,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_work_hours_page_new_by_date_v2(
    begin_date: str,
    end_date: str,
    vincode: str,
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    order_asc: Optional[int] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """按车按日期分页查询运行时间明细 v2。API: GET /apiForAi/v2/queryWorkHoursPageNewByDate。"""
    return query_work_hours_page_new_by_date_v2_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        total=total,
        size=size,
        current=current,
        order_asc=order_asc,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def get_worktime_calendar_list_from_doris_v2(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询客户端设备工作日历列表 v2。API: GET /apiForAi/v2/getWorktimeCalendarListFromDoris。"""
    return get_worktime_calendar_list_from_doris_v2_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_trace_v2(
    begin_time: str,
    end_time: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """设备轨迹查询 v2。API: GET /apiForAi/v2/trace。"""
    return query_trace_v2_tool(
        begin_time=begin_time,
        end_time=end_time,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_customer_vehicle_page_v2(
    total: Optional[int] = None,
    size: Optional[int] = None,
    current: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    search_key: Optional[str] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """客户设备列表分页查询 v2。API: GET /apiForAi/v2/customerVehiclePage。"""
    return query_customer_vehicle_page_v2_tool(
        total=total,
        size=size,
        current=current,
        vehicle_id=vehicle_id,
        search_key=search_key,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_device_fault_page_v2(
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
    """故障告警分页查询 v2。API: GET /apiForAi/v2/deviceFaultPage。"""
    return query_device_fault_page_v2_tool(
        total=total,
        size=size,
        current=current,
        vincode=vincode,
        faultcode=faultcode,
        starttime=starttime,
        endtime=endtime,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def query_core_info_v2(
    begin_date: str,
    end_date: str,
    vincode: str,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """查询核心统计信息（通用）v2。API: POST /apiForAi/v2/queryCoreInfo。"""
    return query_core_info_v2_tool(
        begin_date=begin_date,
        end_date=end_date,
        vincode=vincode,
        token=token,
        language=language,
        base_url=base_url,
    )


@mcp.tool()
def call_service_order_union(
    endpoint: str,
    method: str = "POST",
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    token: Optional[str] = None,
    language: Optional[str] = None,
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
) -> dict:
    """调用保养&报修统一工单接口。

    文档 base: http://10.90.21.125:9085/ixcmg
    endpoint 示例：getPage、add、getDevice、getDeviceSrvOrder、cancelSrvOrder，
    或完整 /serviceOrderUnion/add。
    """
    return call_service_order_union_tool(
        endpoint=endpoint,
        method=method,
        params=params,
        payload=payload,
        token=token,
        language=language,
        base_url=base_url,
        service_base_url=service_base_url,
    )

# Start the server
if __name__ == "__main__":
    refresh_customer_app_token_on_startup()
    mcp.run(transport="stdio")
