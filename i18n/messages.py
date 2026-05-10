from typing import Optional

from clients.customer_app_config import get_config_value

DEFAULT_LANGUAGE = "zh-CN"

_SUPPORTED_LANGUAGES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "en": "en-US",
    "en-us": "en-US",
}

_MESSAGES = {
    "zh-CN": {
        "common.required": "{name} is required.",
        "common.missing_required_fields": "Missing required fields: {fields}",
        "common.unknown_status": "未知状态({value})",
        "common.unknown_type": "未知类型({value})",
        "common.unknown_channel": "未知渠道({value})",
        "common.unknown_value": "未知({value})",
        "service_order.status.0": "待派单",
        "service_order.status.1": "待派工",
        "service_order.status.2": "待接单",
        "service_order.status.3": "待预约",
        "service_order.status.4": "待出发",
        "service_order.status.5": "行程中",
        "service_order.status.6": "服务中",
        "service_order.status.7": "已完结",
        "service_order.status.8": "已完结",
        "service_order.status.10": "待评价",
        "service_order.status.100": "已评价",
        "service_order.status.500": "已取消",
        "service_order.order_type.1": "维修",
        "service_order.order_type.2": "保养",
        "service_order.source_channel.1": "集团 400",
        "service_order.source_channel.2": "服务站 Portal",
        "service_order.source_channel.3": "铁三角 APP",
        "service_order.source_channel.4": "物联网",
        "service_order.source_channel.5": "CRM+",
        "service_order.source_channel.6": "系统自动",
        "service_order.source_channel.7": "客户 APP",
        "service_order.source_channel.8": "集团客户 APP",
        "service_order.shutdown.0": "否",
        "service_order.shutdown.1": "是",
        "service_order.service_mode.1": "现场上门指导",
        "service_order.service_mode.2": "远程指导",
        "service_order.not_belong_to_fixed_device": "Service order does not belong to the fixed device.",
        "fault_repair.submit_failed_generic": "提交维修工单失败，请稍后重试。",
        "fault_repair.device_not_found": "没找到固定设备，无法进行故障报修。",
        "fault_repair.invalid_vincode": "设备编码格式不正确，请说完整设备编码。",
        "fault_repair.init_failed": "暂时无法初始化设备服务，请稍后再试。",
        "fault_repair.fixed_vincode_missing": "固定设备编码缺失，无法进行故障报修。",
        "fault_repair.fixed_vincode_invalid": "固定设备编码不正确，无法进行故障报修。",
        "fault_repair.missing_fields_prefix": "请补充：{fields}",
        "fault_repair.field.fault_description": "故障描述",
        "fault_repair.field.new_contact": "现场联系人姓名",
        "fault_repair.field.new_feedbacktel": "现场联系人电话",
        "fault_repair.field.vincode": "整机编码",
        "fault_repair.confirm_submit": "请确认报修信息并提交工单。",
        "fault_repair.submit_success": "维修服务单创建成功。",
        "fault_repair.confirm_value": "确认",
    },
    "en-US": {
        "common.required": "{name} is required.",
        "common.missing_required_fields": "Missing required fields: {fields}",
        "common.unknown_status": "Unknown status ({value})",
        "common.unknown_type": "Unknown type ({value})",
        "common.unknown_channel": "Unknown channel ({value})",
        "common.unknown_value": "Unknown ({value})",
        "service_order.status.0": "Pending dispatch",
        "service_order.status.1": "Pending assignment",
        "service_order.status.2": "Pending acceptance",
        "service_order.status.3": "Pending appointment",
        "service_order.status.4": "Pending departure",
        "service_order.status.5": "In transit",
        "service_order.status.6": "In service",
        "service_order.status.7": "Completed",
        "service_order.status.8": "Completed",
        "service_order.status.10": "Pending review",
        "service_order.status.100": "Reviewed",
        "service_order.status.500": "Cancelled",
        "service_order.order_type.1": "Repair",
        "service_order.order_type.2": "Maintenance",
        "service_order.source_channel.1": "Group 400",
        "service_order.source_channel.2": "Service Station Portal",
        "service_order.source_channel.3": "Triangular App",
        "service_order.source_channel.4": "IoT",
        "service_order.source_channel.5": "CRM+",
        "service_order.source_channel.6": "System Automatic",
        "service_order.source_channel.7": "Customer App",
        "service_order.source_channel.8": "Group Customer App",
        "service_order.shutdown.0": "No",
        "service_order.shutdown.1": "Yes",
        "service_order.service_mode.1": "On-site guidance",
        "service_order.service_mode.2": "Remote guidance",
        "service_order.not_belong_to_fixed_device": "Service order does not belong to the fixed device.",
        "fault_repair.submit_failed_generic": "Failed to submit the repair work order. Please try again later.",
        "fault_repair.device_not_found": "The fixed device was not found, so fault repair cannot continue.",
        "fault_repair.invalid_vincode": "The device code format is invalid. Please provide the full device code.",
        "fault_repair.init_failed": "The device service is temporarily unavailable. Please try again later.",
        "fault_repair.fixed_vincode_missing": "The fixed device code is missing, so fault repair cannot continue.",
        "fault_repair.fixed_vincode_invalid": "The fixed device code is invalid, so fault repair cannot continue.",
        "fault_repair.missing_fields_prefix": "Please provide: {fields}",
        "fault_repair.field.fault_description": "fault description",
        "fault_repair.field.new_contact": "on-site contact name",
        "fault_repair.field.new_feedbacktel": "on-site contact phone",
        "fault_repair.field.vincode": "device VIN",
        "fault_repair.confirm_submit": "Please confirm the repair details and submit the work order.",
        "fault_repair.submit_success": "Repair service order created successfully.",
        "fault_repair.confirm_value": "Confirm",
    },
}


def get_language(language: Optional[str] = None) -> str:
    raw = (language or get_config_value("language", DEFAULT_LANGUAGE) or DEFAULT_LANGUAGE).strip()
    return _SUPPORTED_LANGUAGES.get(raw.lower(), DEFAULT_LANGUAGE)


def t(key: str, language: Optional[str] = None, **kwargs) -> str:
    resolved_language = get_language(language)
    message = (
        _MESSAGES.get(resolved_language, {}).get(key)
        or _MESSAGES[DEFAULT_LANGUAGE].get(key)
        or key
    )
    if kwargs:
        return message.format(**kwargs)
    return message
