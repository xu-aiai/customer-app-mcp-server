import hashlib
import json
import logging
import re
import time
from json import JSONDecodeError
from typing import Optional
from urllib import error, parse, request

from clients.customer_app import REQUEST_TIMEOUT_SECONDS
from clients.customer_app_config import get_nested_config_value

logger = logging.getLogger("DomesticTelematicsClient")

DEFAULT_BASE_URL = "https://machinery360.hanyunmmip.cn"


class DomesticTelematicsClient:
    """Client for domestic telematics APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_base_url: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        del service_base_url
        self.base_url = (
            base_url
            or get_nested_config_value("domestic_telematics", "base_url")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def query_vehicle_by_vincode(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        del token
        del language
        return self._signed_get(
            "国内车联网设备档案",
            "/third-api/vehicle/getBaseInfo",
            {"vincode": vincode},
        )

    def query_vehicle_by_vincode_v2(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        return self.query_vehicle_by_vincode(
            vincode=vincode,
            token=token,
            language=language,
        )

    def get_customer_condition(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        del token
        del language
        return self._signed_get(
            "国内车联网设备当前工况",
            "/third-api/vehicle/getCurrent",
            {"vincode": vincode},
        )

    def query_current_location(
        self,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        del token
        del language
        return self._signed_get(
            "国内车联网设备当前位置",
            "/third-api/vehicle/getLocation",
            {"vincode": vincode},
        )

    def query_customer_vehicle_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        del token
        del language
        vincode = str(params.get("searchKey") or params.get("vincode") or "").strip()
        if not vincode:
            return {
                "success": False,
                "error": "Domestic telematics requires searchKey or vincode.",
            }
        raw = self.query_vehicle_by_vincode(vincode=vincode)
        if raw.get("success") is False:
            return raw
        records = self._extract_data_list(raw)
        return {
            "code": 0,
            "msg": raw.get("msg"),
            "data": {
                "records": records,
                "total": len(records),
                "current": params.get("current") or 1,
                "size": params.get("size") or len(records) or 1,
            },
        }

    def query_customer_vehicle_page_v2(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        return self.query_customer_vehicle_page(
            token=token,
            language=language,
            **params,
        )

    def query_planned_maintained_item_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        del token
        del language
        vincode = str(params.get("vincode") or "").strip()
        if not vincode:
            return {
                "success": False,
                "error": "Domestic telematics requires vincode.",
            }
        raw = self._signed_get(
            "国内车联网设备保养提醒",
            "/third-api/vehicle/getMaintenanceRemind",
            {"vincode": vincode},
        )
        if raw.get("success") is False:
            return raw
        records = self._extract_data_list(raw)
        current = self._to_int(params.get("current"), default=1)
        size = self._to_int(params.get("size"), default=len(records) or 10)
        start = max(current - 1, 0) * size
        paged = records[start : start + size]
        return {
            "code": 0,
            "msg": raw.get("msg"),
            "data": {
                "records": paged,
                "total": len(records),
                "current": current,
                "size": size,
            },
        }

    def query_planned_maintained_item_page_v2(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        return self.query_planned_maintained_item_page(
            token=token,
            language=language,
            **params,
        )

    def query_trace(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        del token
        del language
        required = {
            "vincode": params.get("vincode"),
            "startTime": params.get("beginTime") or params.get("startTime"),
            "endTime": params.get("endTime"),
        }
        return self._signed_get(
            "国内车联网轨迹回放",
            "/third-api/vehicle/getTrace",
            required,
        )

    def query_trace_v2(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        return self.query_trace(
            token=token,
            language=language,
            **params,
        )

    def query_work_hours_statistic_info_by_vehicle(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        del token
        del language
        return self._query_work_condition(vincode, begin_date, end_date)

    def query_work_hours_statistic_info_by_vehicle_v2(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        return self.query_work_hours_statistic_info_by_vehicle(
            begin_date=begin_date,
            end_date=end_date,
            vincode=vincode,
            token=token,
            language=language,
        )

    def query_work_hours_page_new_by_date(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        del token
        del language
        return self._query_work_condition(
            str(params.get("vincode") or "").strip(),
            str(params.get("beginDate") or ""),
            str(params.get("endDate") or ""),
            force_query_type="1",
        )

    def query_work_hours_page_new_by_date_v2(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        return self.query_work_hours_page_new_by_date(
            token=token,
            language=language,
            **params,
        )

    def query_core_info(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        del token
        del language
        return self._query_work_condition(vincode, begin_date, end_date)

    def query_core_info_v2(
        self,
        begin_date: str,
        end_date: str,
        vincode: str,
        token: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        return self.query_core_info(
            begin_date=begin_date,
            end_date=end_date,
            vincode=vincode,
            token=token,
            language=language,
        )

    def get_worktime_calendar_list_from_doris(self, *args, **kwargs) -> dict:
        del args
        del kwargs
        return self._unsupported("get_worktime_calendar_list_from_doris")

    def get_worktime_calendar_list_from_doris_v2(self, *args, **kwargs) -> dict:
        del args
        del kwargs
        return self._unsupported("get_worktime_calendar_list_from_doris_v2")

    def query_device_fault_page(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        del token
        del language
        return self.query_vehicle_alarm(
            vincode=str(params.get("vincode") or "").strip(),
            start_time=str(params.get("starttime") or params.get("startTime") or ""),
            end_time=str(params.get("endtime") or params.get("endTime") or ""),
            current=self._to_int(params.get("current"), default=1),
            size=self._to_int(params.get("size"), default=20),
        )

    def query_device_fault_page_v2(
        self,
        token: Optional[str] = None,
        language: Optional[str] = None,
        **params,
    ) -> dict:
        return self.query_device_fault_page(
            token=token,
            language=language,
            **params,
        )

    def call_service_order_union(self, *args, **kwargs) -> dict:
        del args
        del kwargs
        return self._unsupported("call_service_order_union")

    def query_work_rate(
        self,
        vincode: str,
        query_date: str,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网开工率统计",
            "/third-api/vehicle/getWorkRate",
            {
                "vincode": vincode,
                "queryDate": query_date,
            },
        )

    def get_work_condition_header(
        self,
        vincode: str,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网工况表头",
            "/third-api/vehicle/getHeader",
            {"vincode": vincode},
        )

    def query_history_work_condition(
        self,
        vincode: str,
        start_time: str,
        end_time: str,
        current: int = 1,
        size: int = 20,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网历史工况",
            "/third-api/vehicle/getHistory",
            {
                "vincode": vincode,
                "startTime": start_time,
                "endTime": end_time,
                "current": current,
                "size": size,
            },
        )

    def get_env_pro_data(
        self,
        vincode: str,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网环保当前工况",
            "/third-api/vehicle/getEnvProData",
            {"vincode": vincode},
        )

    def query_env_pro_history_data(
        self,
        vincode: str,
        start_time: str,
        end_time: str,
        current: int = 1,
        size: int = 20,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网环保历史工况",
            "/third-api/vehicle/getEnvProHistoryData",
            {
                "vincode": vincode,
                "startTime": start_time,
                "endTime": end_time,
                "current": current,
                "size": size,
            },
        )

    def query_vehicle_alarm(
        self,
        vincode: str,
        start_time: str,
        end_time: str,
        current: int = 1,
        size: int = 20,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网故障报警",
            "/third-api/vehicle/getVehicleAlarm",
            {
                "vincode": vincode,
                "startTime": start_time,
                "endTime": end_time,
                "current": current,
                "size": size,
            },
        )

    def query_indicator_data(
        self,
        vincode: str,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网设备指标数据",
            "/third-api/vehicle/getIndicatorData",
            {"vincode": vincode},
        )

    def query_tags_data(
        self,
        vincode: str,
        language: Optional[str] = None,
    ) -> dict:
        del language
        return self._signed_get(
            "国内车联网设备标签数据",
            "/third-api/vehicle/getTagsData",
            {"vincode": vincode},
        )

    def _query_work_condition(
        self,
        vincode: str,
        start_time: str,
        end_time: str,
        force_query_type: Optional[str] = None,
    ) -> dict:
        if not vincode:
            return {"success": False, "error": "Domestic telematics requires vincode."}
        return self._signed_get(
            "国内车联网数据统计",
            "/third-api/vehicle/getWorkCondition",
            {
                "vincode": vincode,
                "startTime": start_time,
                "endTime": end_time,
                "queryType": force_query_type or self._infer_query_type(start_time, end_time),
            },
        )

    def _signed_get(self, api_name: str, path: str, params: dict) -> dict:
        app_id = get_nested_config_value("domestic_telematics", "app_id")
        app_secret = get_nested_config_value("domestic_telematics", "app_secret")
        if not app_id or not app_secret:
            return {
                "success": False,
                "error": "Missing domestic_telematics.app_id or domestic_telematics.app_secret.",
            }

        signed_params = self._build_signed_params(
            params=params,
            app_id=app_id,
            app_secret=app_secret,
        )
        url = self._build_url(path, signed_params)
        headers = {"Accept": "application/json"}
        api_request = request.Request(url, headers=headers, method="GET")
        logger.info(
            "Calling domestic telematics API: name=%s url=%s params=%s",
            api_name,
            url,
            signed_params,
        )
        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
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
            return {
                "success": False,
                "status_code": exc.code,
                "error": response_body,
            }
        except error.URLError as exc:
            return {
                "success": False,
                "error": str(exc.reason),
            }

    def _build_url(self, path: str, params: dict) -> str:
        return f"{self.base_url}/{path.lstrip('/')}?{parse.urlencode(params)}"

    def _build_signed_params(
        self,
        params: dict,
        app_id: str,
        app_secret: str,
        sign_time: Optional[str] = None,
    ) -> dict:
        signed_params = {
            key: value
            for key, value in {
                **params,
                "appId": app_id,
                "signTime": sign_time or str(int(time.time() * 1000)),
            }.items()
            if value is not None and str(value) != ""
        }
        signed_params["sign"] = self._generate_sign(signed_params, app_secret)
        return signed_params

    @staticmethod
    def _generate_sign(params: dict, app_secret: str) -> str:
        filtered_items = [
            (key, value)
            for key, value in params.items()
            if key != "sign" and value is not None and str(value) != ""
        ]
        filtered_items.sort(key=lambda item: item[0])
        string_a = "&".join(f"{key}={value}" for key, value in filtered_items)
        string_sign_temp = f"{string_a}&appSecret={app_secret}"
        return hashlib.md5(string_sign_temp.encode("utf-8")).hexdigest().upper()

    @staticmethod
    def _extract_data_list(raw: dict) -> list[dict]:
        payload = raw.get("data")
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    @staticmethod
    def _to_int(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _infer_query_type(start_time: str, end_time: str) -> str:
        del end_time
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_time or ""):
            return "1"
        if re.fullmatch(r"\d{4}-\d{2}", start_time or ""):
            return "2"
        if re.fullmatch(r"\d{4}", start_time or ""):
            return "3"
        return "1"

    @staticmethod
    def _unsupported(method_name: str) -> dict:
        return {
            "success": False,
            "error": f"Domestic telematics does not support {method_name} yet.",
        }
