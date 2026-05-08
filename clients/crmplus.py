import json
import os
import time
from json import JSONDecodeError
from typing import Any, Dict, Optional
from urllib import error, parse, request

from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_CRMPLUS_BASE_URL = "http://10.188.4.118:8089"


class CRMPlusClient:
    """CRM+ API client for creating service work orders."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("CRMPLUS_BASE_URL") or DEFAULT_CRMPLUS_BASE_URL
        ).rstrip("/")
        self.app_id = app_id if app_id is not None else os.getenv("CRMPLUS_APP_ID", "")
        self.app_secret = (
            app_secret if app_secret is not None else os.getenv("CRMPLUS_APP_SECRET", "")
        )
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._token_expire_time = 0.0

    def create_repair_order(
        self,
        contact: str,
        feedback_tel: str,
        userprofile_code: str,
        memo: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.create_work_order(
            service_type=0,
            contact=contact,
            feedback_tel=feedback_tel,
            userprofile_code=userprofile_code,
            memo=memo,
            **kwargs,
        )

    def create_work_order(
        self,
        service_type: int,
        contact: str,
        feedback_tel: str,
        userprofile_code: str,
        memo: str,
        servicecategorycode: Optional[str] = None,
        accepttime: Optional[str] = None,
        province_code: Optional[str] = None,
        city_code: Optional[str] = None,
        county_code: Optional[str] = None,
        address: Optional[str] = None,
        organisation_code: Optional[str] = None,
        maintenancetype_name: Optional[str] = None,
        source: int = 7,
        request_dispatch_personnel: Optional[int] = None,
        worker_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._require_config()
        payload: Dict[str, Any] = {
            "new_type": service_type,
            "new_contact": contact,
            "new_feedbacktel": feedback_tel,
            "new_userprofile_code": userprofile_code,
            "new_memo": memo,
            "new_source": source,
        }
        optional_fields = {
            "new_servicecategorycode": servicecategorycode,
            "new_accepttime": accepttime,
            "new_province_code": province_code,
            "new_city_code": city_code,
            "new_county_code": county_code,
            "new_address": address,
            "new_organisation_code": organisation_code,
            "new_srv_maintenancetype_name": maintenancetype_name,
            "new_request_dispatch_personnel": request_dispatch_personnel,
            "new_srv_worker_code": worker_code,
        }
        payload.update(
            {
                key: value
                for key, value in optional_fields.items()
                if value is not None and value != ""
            }
        )

        result = self._post_json("/api/service/CreateWorkOrder", payload, self._headers())
        error_code = result.get("ErrorCode", -1)
        if error_code == 0:
            return result.get("Data", {})
        raise ValueError(result.get("Message") or "创建服务单失败")

    def _headers(self) -> Dict[str, str]:
        token = self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expire_time - 300:
            return self._access_token

        self._require_config()
        body = parse.urlencode(
            {
                "grant_type": "application",
                "appid": self.app_id,
                "appsecret": self.app_secret,
            }
        ).encode("utf-8")
        api_request = request.Request(
            f"{self.base_url}/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        result = self._send(api_request)
        token = result.get("access_token")
        if not token:
            raise ValueError(result.get("message") or "获取 CRM+ Token 失败")
        self._access_token = token
        self._token_expire_time = time.time() + 7200
        return token

    def _post_json(
        self,
        path: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        api_request = request.Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        return self._send(api_request)

    def _send(self, api_request: request.Request) -> Dict[str, Any]:
        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                if not response_body:
                    return {}
                return json.loads(response_body)
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(response_body)
            except JSONDecodeError:
                payload = {"error": response_body}
            raise ValueError(payload.get("Message") or payload.get("error") or str(exc))
        except error.URLError as exc:
            raise ValueError(f"请求 CRM+ 接口失败: {exc.reason}")
        except JSONDecodeError as exc:
            raise ValueError(f"CRM+ 响应不是合法 JSON: {exc}")

    def _require_config(self) -> None:
        missing = []
        if not self.base_url:
            missing.append("CRMPLUS_BASE_URL")
        if not self.app_id:
            missing.append("CRMPLUS_APP_ID")
        if not self.app_secret:
            missing.append("CRMPLUS_APP_SECRET")
        if missing:
            raise ValueError(f"Missing CRM+ config: {', '.join(missing)}")


def create_repair_order(
    contact: str,
    feedback_tel: str,
    userprofile_code: str,
    memo: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    return CRMPlusClient().create_repair_order(
        contact=contact,
        feedback_tel=feedback_tel,
        userprofile_code=userprofile_code,
        memo=memo,
        **kwargs,
    )
