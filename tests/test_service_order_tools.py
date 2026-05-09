import os
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.service_order_tools import (
    FIXED_VINCODE,
    get_service_order_detail_tool,
    list_service_orders_tool,
)


class FakeServiceOrderClient:
    def __init__(self, base_url=None, service_base_url=None):
        self.base_url = base_url
        self.service_base_url = service_base_url

    def fetch_orders(self, app_token=None, **kwargs):
        FakeServiceOrderClient.last_app_token = app_token
        FakeServiceOrderClient.last_vincode = kwargs.get("vincode")
        return [
            {
                "id": "order-1",
                "deviceVin": FIXED_VINCODE,
                "status": 1,
                "orderType": 1,
            }
        ]

    def fetch_order_detail(self, app_token=None, order_id=None, **kwargs):
        FakeServiceOrderClient.last_app_token = app_token
        return {
            "id": order_id,
            "deviceVin": FIXED_VINCODE,
            "status": 1,
            "orderType": 1,
        }


class ServiceOrderToolsTokenTest(unittest.TestCase):
    def setUp(self):
        FakeServiceOrderClient.last_app_token = "unset"
        FakeServiceOrderClient.last_vincode = "unset"

    def test_list_orders_uses_customer_app_token_when_provided(self):
        with patch(
            "tools.service_order_tools.ServiceOrderClient",
            FakeServiceOrderClient,
        ):
            result = list_service_orders_tool(app_token="customer-app-token")

        self.assertTrue(result["success"])
        self.assertEqual(FakeServiceOrderClient.last_app_token, "customer-app-token")
        self.assertEqual(FakeServiceOrderClient.last_vincode, FIXED_VINCODE)

    def test_list_orders_allows_config_token_when_no_token_argument(self):
        with patch(
            "tools.service_order_tools.ServiceOrderClient",
            FakeServiceOrderClient,
        ):
            result = list_service_orders_tool()

        self.assertTrue(result["success"])
        self.assertIsNone(FakeServiceOrderClient.last_app_token)
        self.assertEqual(FakeServiceOrderClient.last_vincode, FIXED_VINCODE)

    def test_detail_uses_xcmg_customer_app_token_when_provided(self):
        with patch(
            "tools.service_order_tools.ServiceOrderClient",
            FakeServiceOrderClient,
        ):
            result = get_service_order_detail_tool(
                order_id="order-1",
                xcmg_app_token="xcmg-customer-app-token",
            )

        self.assertTrue(result["success"])
        self.assertEqual(
            FakeServiceOrderClient.last_app_token,
            "xcmg-customer-app-token",
        )

    def test_detail_rejects_order_for_other_device(self):
        class OtherDeviceClient(FakeServiceOrderClient):
            def fetch_order_detail(self, app_token=None, order_id=None, **kwargs):
                return {
                    "id": order_id,
                    "deviceVin": "XUGY215LCRKA00005",
                    "status": 1,
                    "orderType": 1,
                }

        with patch(
            "tools.service_order_tools.ServiceOrderClient",
            OtherDeviceClient,
        ):
            result = get_service_order_detail_tool(order_id="order-1")

        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
