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
from tools.customer_app_tools import query_vehicle_by_vincode_tool


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
            start_time="2026-01-01 00:00:00",
            end_time="2026-01-02 00:00:00",
            current=2,
            size=10,
        )


if __name__ == "__main__":
    unittest.main()
