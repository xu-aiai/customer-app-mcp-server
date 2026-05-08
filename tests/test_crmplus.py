import os
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from clients.crmplus import CRMPlusClient


class CRMPlusClientConfigTest(unittest.TestCase):
    def test_crmplus_config_comes_from_config_not_environment(self):
        values = {
            "crmplus_base_url": "https://config-crmplus.example.com",
            "crmplus_app_id": "config-app",
            "crmplus_app_secret": "config-secret",
        }
        with patch.dict(
            os.environ,
            {
                "CRMPLUS_BASE_URL": "https://env-crmplus.example.com",
                "CRMPLUS_APP_ID": "env-app",
                "CRMPLUS_APP_SECRET": "env-secret",
            },
            clear=False,
        ), patch(
            "clients.crmplus.get_config_value",
            side_effect=lambda key, default=None: values.get(key, default),
        ):
            client = CRMPlusClient()

        self.assertEqual(client.base_url, "https://config-crmplus.example.com")
        self.assertEqual(client.app_id, "config-app")
        self.assertEqual(client.app_secret, "config-secret")

    def test_explicit_values_still_take_precedence(self):
        values = {
            "crmplus_base_url": "https://config-crmplus.example.com",
            "crmplus_app_id": "config-app",
            "crmplus_app_secret": "config-secret",
        }
        with patch(
            "clients.crmplus.get_config_value",
            side_effect=lambda key, default=None: values.get(key, default),
        ):
            client = CRMPlusClient(
                base_url="https://explicit-crmplus.example.com",
                app_id="explicit-app",
                app_secret="explicit-secret",
            )

        self.assertEqual(client.base_url, "https://explicit-crmplus.example.com")
        self.assertEqual(client.app_id, "explicit-app")
        self.assertEqual(client.app_secret, "explicit-secret")

    def test_create_work_order_sends_gcapp_order_id(self):
        client = CRMPlusClient(
            base_url="https://config-crmplus.example.com",
            app_id="config-app",
            app_secret="config-secret",
        )

        with patch.object(client, "_headers", return_value={}), patch.object(
            client,
            "_post_json",
            return_value={"ErrorCode": 0, "Data": {"new_code": "WO-1"}},
        ) as post_json, patch(
            "clients.crmplus.uuid.uuid4",
            return_value="abcdef12-3456-7890-abcd-ef1234567890",
        ):
            result = client.create_repair_order(
                contact="张三",
                feedback_tel="13800138000",
                userprofile_code="XUGY215LCRKA00005",
                memo="发动机无法启动",
            )

        self.assertEqual(result, {"new_code": "WO-1"})
        payload = post_json.call_args.args[1]
        self.assertEqual(payload["gcappOrderId"], "ABCDEF12")
        self.assertEqual(payload["new_type"], 0)
        self.assertEqual(payload["new_source"], 7)


if __name__ == "__main__":
    unittest.main()
