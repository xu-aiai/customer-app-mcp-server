import os
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from clients.domestic_telematics import DomesticTelematicsClient
from clients.telematics_bridge import (
    DOMESTIC_PROVIDER,
    OVERSEAS_PROVIDER,
    get_telematics_provider,
)
from tools.customer_app_tools import (
    FIXED_VINCODE,
    _resolve_vincode,
    query_device_fault_page_tool,
    query_vehicle_by_vincode_tool,
)


class FakeDomesticClient:
    def __init__(self, base_url=None, service_base_url=None, timeout=30):
        self.base_url = base_url
        self.service_base_url = service_base_url
        self.timeout = timeout

    def query_vehicle_by_vincode(self, vincode, token=None, language=None):
        return {
            "code": 0,
            "msg": None,
            "data": [
                {
                    "vincode": vincode,
                    "companyName": "徐工",
                }
            ],
        }


class FakeFaultPageClient:
    def query_device_fault_page(self, **kwargs):
        del kwargs
        return {
            "code": 1,
            "msg": "参数错误:startTime: 开始时间不能为空; endTime: 结束时间不能为空",
            "data": None,
        }


class DomesticTelematicsTest(unittest.TestCase):
    def test_generate_sign_uses_ascii_sorted_key_value_pairs(self):
        sign = DomesticTelematicsClient._generate_sign(
            {
                "appId": "wxd930ea5d5a258f4f",
                "vincode": "XUG0450GPDHJ00023",
                "signTime": "1728962564813",
            },
            "192006250b4c09247ec02edce69f6a2d",
        )

        self.assertEqual(sign, "96ED9AFFA7FDF316E7A1F6220675DFB0")

    def test_provider_defaults_to_domestic(self):
        with patch(
            "clients.telematics_bridge.get_config_value",
            return_value=None,
        ):
            self.assertEqual(get_telematics_provider(), DOMESTIC_PROVIDER)

    def test_provider_can_switch_to_overseas(self):
        with patch(
            "clients.telematics_bridge.get_config_value",
            return_value=OVERSEAS_PROVIDER,
        ):
            self.assertEqual(get_telematics_provider(), OVERSEAS_PROVIDER)

    def test_query_vehicle_tool_uses_bridge_client(self):
        with patch(
            "tools.customer_app_tools.create_telematics_client",
            return_value=FakeDomesticClient(),
        ):
            result = query_vehicle_by_vincode_tool(vincode="XUG0450GPDHJ00023")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["data"][0]["companyName"],
            "徐工",
        )

    def test_domestic_mode_uses_fixed_vincode(self):
        with patch(
            "tools.customer_app_tools.get_telematics_provider",
            return_value=DOMESTIC_PROVIDER,
        ):
            self.assertEqual(_resolve_vincode("VIN001"), FIXED_VINCODE)

    def test_overseas_mode_uses_requested_vincode(self):
        with patch(
            "tools.customer_app_tools.get_telematics_provider",
            return_value=OVERSEAS_PROVIDER,
        ):
            self.assertEqual(_resolve_vincode("VIN001"), "VIN001")

    def test_query_type_inference(self):
        self.assertEqual(
            DomesticTelematicsClient._infer_query_type("2026-05-01", "2026-05-09"),
            "1",
        )
        self.assertEqual(
            DomesticTelematicsClient._infer_query_type("2026-05", "2026-06"),
            "2",
        )
        self.assertEqual(
            DomesticTelematicsClient._infer_query_type("2026", "2027"),
            "3",
        )

    def test_get_customer_condition_calls_current_endpoint(self):
        client = DomesticTelematicsClient(base_url="https://example.com")

        with patch.object(
            client,
            "_signed_get",
            return_value={"code": 0, "data": []},
        ) as mock_signed_get:
            client.get_customer_condition("VIN001")

        mock_signed_get.assert_called_once_with(
            "国内车联网设备当前工况",
            "/third-api/vehicle/getCurrent",
            {"vincode": "VIN001"},
        )

    def test_query_device_fault_page_delegates_to_vehicle_alarm(self):
        client = DomesticTelematicsClient(base_url="https://example.com")

        with patch.object(
            client,
            "query_vehicle_alarm",
            return_value={"code": 0, "data": {}},
        ) as mock_alarm:
            client.query_device_fault_page(
                current=2,
                size=10,
                vincode="VIN001",
                starttime="2026-01-01 00:00:00",
                endtime="2026-01-02 00:00:00",
            )

        mock_alarm.assert_called_once_with(
            vincode="VIN001",
            start_time="2026-01-01",
            end_time="2026-01-02",
            current=2,
            size=10,
        )

    def test_query_device_fault_page_preserves_date_only_inputs(self):
        client = DomesticTelematicsClient(base_url="https://example.com")

        with patch.object(
            client,
            "query_vehicle_alarm",
            return_value={"code": 0, "data": {}},
        ) as mock_alarm:
            client.query_device_fault_page(
                current=1,
                size=20,
                vincode="VIN001",
                starttime="2026-01-01",
                endtime="2026-01-02",
            )

        mock_alarm.assert_called_once_with(
            vincode="VIN001",
            start_time="2026-01-01",
            end_time="2026-01-02",
            current=1,
            size=20,
        )

    def test_query_device_fault_tool_requires_dates_in_domestic_mode(self):
        with patch(
            "tools.customer_app_tools.get_telematics_provider",
            return_value=DOMESTIC_PROVIDER,
        ):
            result = query_device_fault_page_tool(vincode="VIN001", size=10)

        self.assertEqual(result, {"success": False, "error": "starttime is required."})

    def test_query_device_fault_tool_localizes_known_param_error_for_english(self):
        with patch(
            "tools.customer_app_tools._client",
            return_value=FakeFaultPageClient(),
        ):
            result = query_device_fault_page_tool(
                vincode="VIN001",
                size=10,
                current=1,
                starttime="2026-01-01",
                endtime="2026-01-02",
                language="en-US",
            )

        self.assertEqual(
            result["data"]["msg"],
            "Invalid parameters: startTime is required; endTime is required.",
        )


if __name__ == "__main__":
    unittest.main()
