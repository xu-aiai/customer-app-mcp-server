import json
import logging
from json import JSONDecodeError
from typing import Optional
from urllib import error, parse, request

from clients.customer_app_config import (
    get_config_value,
    get_customer_app_token,
)

logger = logging.getLogger("CustomerAppClient")

REQUEST_TIMEOUT_SECONDS = 30


def build_request_headers(
    token: Optional[str] = None,
    language: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    """Build common headers for customer app API requests.

    All customer app APIs use the same Authorization and Lang headers. Keep
    this in one place so future API methods do not duplicate header assembly.
    """
    resolved_token = token or get_customer_app_token()
    resolved_language = language or get_config_value("language", "zh-CN")

    if not resolved_token:
        raise ValueError(
            "Missing token. Run scripts/fetch_customer_app_token.py to write token to config."
        )

    headers = {
        "Authorization": f"Bearer {resolved_token}",
        "Lang": resolved_language,
        "Accept": "application/json",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


class CustomerAppClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = (
            base_url
            or get_config_value("api_base_url")
        ).rstrip("/")
        self.timeout = timeout

    def query_vehicle_by_vincode(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """通过 vincode 查询车辆.

        GET /apiForAi/customerVehicle/{vincode}
        Path params:
        - vincode: 设备编码/车架号.
        """
        headers = build_request_headers(token=token, language=language)
        encoded_vincode = parse.quote(vincode.strip(), safe="")
        return self._get(
            "通过 vincode 查询车辆",
            f"/apiForAi/customerVehicle/{encoded_vincode}",
            headers,
        )

    def query_work_hours_statistic_info_by_vehicle(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """按车统计运行时间统计信息查询.

        POST /apiForAi/queryWorkHoursStatisticInfoByVehicle
        JSON body:
        - beginDate: 开始日期, yyyy-MM-dd.
        - endDate: 结束日期, yyyy-MM-dd.
        - vincode: 设备编码/车架号.
        """
        headers = build_request_headers(
            token=token,
            language=language,
            content_type="application/json",
        )
        return self._post_json(
            "按车统计运行时间统计信息查询",
            "/apiForAi/queryWorkHoursStatisticInfoByVehicle",
            {
                "beginDate": begin_date,
                "endDate": end_date,
                "vincode": vincode,
            },
            headers,
        )

    def query_planned_maintained_item_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """计划维保分页查询.

        GET /apiForAi/queryPlannedMaintainedItemPage
        Query params:
        - current/size/total: 分页参数.
        - beginDate/endDate: 提醒开始/结束日期, yyyy-MM-dd.
        - vincode: 车架号.
        - itemName: 计划名称模糊搜索条件.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get(
            "计划维保分页查询",
            "/apiForAi/queryPlannedMaintainedItemPage",
            headers,
            params,
        )

    def get_customer_condition(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """获取当前工况.

        GET /customerApp/getCustomerCondition
        Query params:
        - vincode: 车架号.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get(
            "获取当前工况",
            "/customerApp/getCustomerCondition",
            headers,
            {"vincode": vincode},
        )

    def query_work_hours_page_new_by_date(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """按车按日期统计运行时间分页接口.

        GET /apiForAi/queryWorkHoursPageNewByDate
        Query params:
        - current/size/total: 分页参数.
        - beginDate/endDate: 开始/结束日期, yyyy-MM-dd.
        - vincode: 设备编码.
        - orderAsc: 排序顺序, 1 表示时间正序, 默认倒序.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get(
            "按车按日期统计运行时间分页接口",
            "/apiForAi/queryWorkHoursPageNewByDate",
            headers,
            params,
        )

    def get_worktime_calendar_list_from_doris(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """查询客户端设备工作日历 List.

        GET /apiForAi/getWorktimeCalendarListFromDoris
        Query params:
        - beginDate/endDate: 开始/结束日期, yyyy-MM-dd.
        - vincode: 设备编码.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get(
            "查询客户端设备工作日历 List",
            "/apiForAi/getWorktimeCalendarListFromDoris",
            headers,
            params,
        )

    def query_trace(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """设备轨迹.

        GET /apiForAi/trace
        Query params:
        - beginTime/endTime: 开始/结束时间, yyyy-MM-dd HH:mm:ss.
        - vincode: 设备编码.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get("设备轨迹", "/apiForAi/trace", headers, params)

    def query_customer_vehicle_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """客户设备列表.

        GET /apiForAi/customerVehiclePage
        Query params:
        - current/size/total: 分页参数.
        - id: 车辆 id.
        - searchKey: 设备名称/设备编码.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get("客户设备列表", "/apiForAi/customerVehiclePage", headers, params)

    def query_device_fault_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        """故障告警分页查询.

        GET /apiForAi/deviceFaultPage
        Query params:
        - current/size/total: 分页参数.
        - vincode: 设备编码.
        - faultcode: 故障代码.
        - starttime/endtime: 开始/结束时间.
        """
        headers = build_request_headers(token=token, language=language)
        return self._get("故障告警分页查询", "/apiForAi/deviceFaultPage", headers, params)

    def query_core_info(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """查询核心统计信息（通用）.

        POST /apiForAi/queryCoreInfo
        JSON body:
        - beginDate: 开始日期, yyyy-MM-dd.
        - endDate: 结束日期, yyyy-MM-dd.
        - vincode: 设备编码/车架号.
        """
        headers = build_request_headers(
            token=token,
            language=language,
            content_type="application/json",
        )
        return self._post_json(
            "查询核心统计信息（通用）",
            "/apiForAi/queryCoreInfo",
            {
                "beginDate": begin_date,
                "endDate": end_date,
                "vincode": vincode,
            },
            headers,
        )

    def _get(
        self,
        api_name: str,
        path: str,
        headers: dict,
        params: Optional[dict] = None,
    ) -> dict:
        url = self._build_url(path, params)
        api_request = request.Request(url, headers=headers, method="GET")
        return self._send(api_name, api_request, params=params)

    def _post_json(self, api_name: str, path: str, payload: dict, headers: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        api_request = request.Request(
            self._build_url(path),
            data=body,
            headers=headers,
            method="POST",
        )
        return self._send(api_name, api_request, payload=payload)

    def _build_url(self, path: str, params: Optional[dict] = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        cleaned_params = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        if not cleaned_params:
            return url
        return f"{url}?{parse.urlencode(cleaned_params)}"

    def _send(
        self,
        api_name: str,
        api_request: request.Request,
        params: Optional[dict] = None,
        payload: Optional[dict] = None,
    ) -> dict:
        method = api_request.get_method()
        safe_headers = self._mask_headers(dict(api_request.header_items()))
        logger.info(
            "Calling customer app API: name=%s method=%s url=%s params=%s payload=%s headers=%s",
            api_name,
            method,
            api_request.full_url,
            self._clean_log_data(params),
            self._clean_log_data(payload),
            safe_headers,
        )
        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                logger.info(
                    "Customer app API response: name=%s status=%s bytes=%s",
                    api_name,
                    response.status,
                    len(response_body.encode("utf-8")),
                )
                if not response_body:
                    return {}
                try:
                    return json.loads(response_body)
                except JSONDecodeError:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": "Response is not valid JSON.",
                        "response": response_body,
                    }
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            logger.warning(
                "Customer app API HTTP error: name=%s status=%s body=%s",
                api_name,
                exc.code,
                response_body,
            )
            return {
                "success": False,
                "status_code": exc.code,
                "error": response_body,
            }
        except error.URLError as exc:
            logger.warning(
                "Customer app API request error: name=%s reason=%s",
                api_name,
                exc.reason,
            )
            return {
                "success": False,
                "error": str(exc.reason),
            }

    def _clean_log_data(self, data: Optional[dict]) -> dict:
        return {
            key: value
            for key, value in (data or {}).items()
            if value is not None and value != ""
        }

    def _mask_headers(self, headers: dict) -> dict:
        masked_headers = dict(headers)
        authorization = masked_headers.get("Authorization")
        if authorization:
            masked_headers["Authorization"] = self._mask_authorization(authorization)
        return masked_headers

    def _mask_authorization(self, authorization: str) -> str:
        if len(authorization) <= 16:
            return "***"
        return f"{authorization[:10]}...{authorization[-4:]}"
