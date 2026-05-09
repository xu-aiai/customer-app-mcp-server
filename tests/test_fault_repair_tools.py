import os
import sys
import types
import unittest
from unittest.mock import patch

from clients.crmplus import CRMPlusClient


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

fake_crmplus_client = types.ModuleType("clients.crmplus_client")
fake_crmplus_client.create_repair_order = lambda **kwargs: {}
sys.modules.setdefault("clients.crmplus_client", fake_crmplus_client)

from tools.fault_repair_tools import (
    FIXED_VINCODE,
    prepare_fault_repair_tool,
    submit_fault_repair_order_tool,
)


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


def _detail_response(vincode=FIXED_VINCODE):
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
    def test_prepare_without_vincode_uses_fixed_device(self):
        fake = FakeCustomerAppClient(
            vehicle_detail=_detail_response(),
        )

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool()

        self.assertTrue(result["success"])
        self.assertEqual(fake.detail_calls, [FIXED_VINCODE])
        self.assertEqual(result["action"], "ask_missing_info")
        self.assertEqual(result["state"]["vincode"], FIXED_VINCODE)

    def test_prepare_ignores_device_selection_state_and_uses_fixed_vincode(self):
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

        self.assertEqual(fake.detail_calls, [FIXED_VINCODE])
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "confirm_submit")
        self.assertEqual(result["submit_payload"]["deviceVin"], FIXED_VINCODE)
        self.assertNotIn("devices", result["state"])

    def test_submit_workorder_payload_contains_frontend_fields(self):
        fake = FakeCustomerAppClient(vehicle_detail=_detail_response())

        with patch("tools.fault_repair_tools.CustomerAppClient", return_value=fake):
            result = prepare_fault_repair_tool(
                vincode="XUGY215LCRKA00005",
                fault_description="GPS电源坏了",
                new_contact="小徐",
                new_feedbacktel="18888106769",
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "confirm_submit")
        self.assertEqual(
            result["submit_payload"],
            {
                "value": "确认",
                "action": "confirm_work_order",
                "type": "submitWorkorder",
                "deviceVin": FIXED_VINCODE,
                "faultDescription": "GPS电源坏了",
                "deviceId": "vehicle-1",
                "deviceModel": "XE215",
                "detailAddress": "徐州",
                "deviceName": "挖掘机",
                "contactName": "小徐",
                "contactPhone": "18888106769",
            },
        )

    def test_invalid_vincode_is_ignored_and_fixed_device_is_used(self):
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

        self.assertEqual(fake.detail_calls, [FIXED_VINCODE])
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "ask_missing_info")
        self.assertEqual(result["state"]["vincode"], FIXED_VINCODE)

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

        self.assertEqual(fake.detail_calls, [FIXED_VINCODE])
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "没找到固定设备，无法进行故障报修。")
        self.assertNotIn("very long stack trace", str(result))

    def test_submit_order_ignores_payload_and_argument_device_vin(self):
        calls = []

        def fake_create_repair_order(**kwargs):
            calls.append(kwargs)
            return {"id": "order-1"}

        with patch(
            "tools.fault_repair_tools.create_repair_order",
            side_effect=fake_create_repair_order,
        ):
            result = submit_fault_repair_order_tool(
                payload={
                    "deviceVin": "XUGY215LCRKA00005",
                    "faultDescription": "GPS电源坏了",
                    "contactName": "小徐",
                    "contactPhone": "18888106769",
                },
                device_vin="XUGY215LCRKA00006",
            )

        self.assertTrue(result["success"])
        self.assertEqual(calls[0]["userprofile_code"], FIXED_VINCODE)

    def test_submit_order_failure_uses_submit_failed_action(self):
        with patch(
            "tools.fault_repair_tools.create_repair_order",
            side_effect=ValueError("-1"),
        ):
            result = submit_fault_repair_order_tool(
                payload={
                    "faultDescription": "GPS电源坏了",
                    "contactName": "小徐",
                    "contactPhone": "18888106769",
                }
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["action"], "submit_failed")
        self.assertEqual(result["message"], "提交维修工单失败，请稍后重试。")


class CRMPlusClientTest(unittest.TestCase):
    def test_invalid_crmplus_message_falls_back_to_error_code(self):
        client = CRMPlusClient(
            base_url="https://crmplus.example.com",
            app_id="app-id",
            app_secret="app-secret",
        )

        with patch.object(client, "_headers", return_value={}):
            with patch.object(
                client,
                "_post_json",
                return_value={"ErrorCode": -1, "Message": "-1"},
            ):
                with self.assertRaises(ValueError) as ctx:
                    client.create_repair_order(
                        contact="小徐",
                        feedback_tel="18888106769",
                        userprofile_code=FIXED_VINCODE,
                        memo="GPS电源坏了",
                    )

        self.assertEqual(str(ctx.exception), "CRM+ 创建服务单失败（ErrorCode: -1）")


if __name__ == "__main__":
    unittest.main()
