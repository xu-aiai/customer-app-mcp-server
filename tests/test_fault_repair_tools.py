import os
import sys
import types
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

fake_crmplus_client = types.ModuleType("clients.crmplus_client")
fake_crmplus_client.create_repair_order = lambda **kwargs: {}
sys.modules.setdefault("clients.crmplus_client", fake_crmplus_client)

from tools.fault_repair_tools import prepare_fault_repair_tool


class FakeCustomerAppClient:
    def __init__(
        self,
        vehicle_page=None,
        vehicle_detail=None,
    ):
        self.vehicle_page = vehicle_page or {}
        self.vehicle_detail = vehicle_detail or {}
        self.detail_calls = []

    def query_customer_vehicle_page(self, **kwargs):
        return self.vehicle_page

    def query_vehicle_by_vincode(self, vincode, **kwargs):
        self.detail_calls.append(vincode)
        return self.vehicle_detail


def _detail_response(vincode="XUGY215LCRKA00005"):
    return {
        "data": {
            "id": "vehicle-1",
            "vincode": vincode,
            "modelTypeName": "XE215",
            "productTypeName": "挖掘机",
            "address": "徐州",
        }
    }


class PrepareFaultRepairToolTest(unittest.TestCase):
    def test_select_device_returns_voice_response_and_indexed_devices(self):
        fake = FakeCustomerAppClient(
            vehicle_page={
                "code": 0,
                "data": {
                    "items": [
                        {
                            "vincode": "XUGY215LCRKA00005",
                            "id": "vehicle-1",
                            "productTypeName": "挖掘机",
                        },
                        {
                            "vincode": "XUGY215LCRKA00006",
                            "id": "vehicle-2",
                            "productTypeName": "装载机",
                        },
                    ]
                },
            }
        )

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool()

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "select_device")
        self.assertEqual(result["response"], "你名下有2台设备，请说第几辆，或者直接说设备编码。")
        self.assertEqual(result["devices"][0]["index"], 1)
        self.assertEqual(result["state"]["devices"][1]["label"], "第2辆")

    def test_ordinal_device_selection_resolves_to_real_vincode(self):
        fake = FakeCustomerAppClient(vehicle_detail=_detail_response())
        state = {
            "devices": [
                {"vincode": "XUGY215LCRKA00005", "deviceName": "挖掘机"},
                {"vincode": "XUGY215LCRKA00006", "deviceName": "装载机"},
            ]
        }

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool(
                user_message="第一辆车",
                session_state=state,
                fault_description="发动机无法启动",
                new_contact="张三",
                new_feedbacktel="13800138000",
            )

        self.assertEqual(fake.detail_calls, ["XUGY215LCRKA00005"])
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "confirm_submit")
        self.assertEqual(result["submit_payload"]["deviceVin"], "XUGY215LCRKA00005")

    def test_invalid_vincode_with_devices_returns_recoverable_error_without_backend_call(self):
        fake = FakeCustomerAppClient(vehicle_detail=_detail_response())
        state = {
            "devices": [
                {"vincode": "XUGY215LCRKA00005", "deviceName": "挖掘机"},
            ]
        }

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool(
                session_state=state,
                vincode="测试0005",
            )

        self.assertEqual(fake.detail_calls, [])
        self.assertFalse(result["success"])
        self.assertEqual(result["action"], "ask_missing_info")
        self.assertEqual(result["message"], "没找到这台设备，请说第几辆或完整设备编码。")
        self.assertEqual(result["response"], result["message"])

    def test_backend_detail_error_is_compressed(self):
        fake = FakeCustomerAppClient(
            vehicle_detail={
                "success": False,
                "status_code": 500,
                "error": "java.lang.RuntimeException: very long stack trace",
            }
        )

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool(vincode="XUGY215LCRKA00005")

        self.assertEqual(fake.detail_calls, ["XUGY215LCRKA00005"])
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "没找到这台设备，请说第几辆或完整设备编码。")
        self.assertNotIn("very long stack trace", str(result))


if __name__ == "__main__":
    unittest.main()
