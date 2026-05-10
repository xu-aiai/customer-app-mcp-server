import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = ROOT / "mcp_server.py"


class MCPServerDocstringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MCP_SERVER.read_text(encoding="utf-8")

    def assert_tool_contains(self, tool_name: str, snippets: list[str]) -> None:
        pattern = rf"def {re.escape(tool_name)}\([^)]*\)\s*-> dict:\n\s+\"\"\"(.*?)\"\"\""
        match = re.search(pattern, self.source, re.S)
        self.assertIsNotNone(match, f"Docstring not found for {tool_name}")
        doc = match.group(1)
        for snippet in snippets:
            self.assertIn(snippet, doc, f"{tool_name} missing snippet: {snippet}")

    def test_time_related_tools_document_parameter_formats(self):
        expectations = {
            "query_work_hours_statistic_info_by_vehicle": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_planned_maintained_item_page": [
                "begin_date: 提醒开始日期，格式 yyyy-MM-dd。",
                "end_date: 提醒结束日期，格式 yyyy-MM-dd。",
            ],
            "query_work_hours_page_new_by_date": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "get_worktime_calendar_list_from_doris": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_trace": [
                "begin_time: 开始时间，格式 yyyy-MM-dd HH:mm:ss。",
                "end_time: 结束时间，格式 yyyy-MM-dd HH:mm:ss。",
            ],
            "query_device_fault_page": [
                "starttime: 开始日期，格式 yyyy-MM-dd。",
                "endtime: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_work_rate": [
                "query_date: 查询月份，格式 yyyy-MM。",
            ],
            "query_history_work_condition": [
                "start_time: 开始时间，格式 yyyy-MM-dd HH:mm:ss。",
                "end_time: 结束时间，格式 yyyy-MM-dd HH:mm:ss。",
            ],
            "query_env_pro_history_data": [
                "start_time: 开始时间，格式 yyyy-MM-dd HH:mm:ss。",
                "end_time: 结束时间，格式 yyyy-MM-dd HH:mm:ss。",
            ],
            "query_vehicle_alarm": [
                "start_time: 开始日期，格式 yyyy-MM-dd。",
                "end_time: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_core_info": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_work_hours_statistic_info_by_vehicle_v2": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_planned_maintained_item_page_v2": [
                "begin_date: 提醒开始日期，格式 yyyy-MM-dd。",
                "end_date: 提醒结束日期，格式 yyyy-MM-dd。",
            ],
            "query_work_hours_page_new_by_date_v2": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "get_worktime_calendar_list_from_doris_v2": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_trace_v2": [
                "begin_time: 开始时间，格式 yyyy-MM-dd HH:mm:ss。",
                "end_time: 结束时间，格式 yyyy-MM-dd HH:mm:ss。",
            ],
            "query_device_fault_page_v2": [
                "starttime: 开始日期，格式 yyyy-MM-dd。",
                "endtime: 结束日期，格式 yyyy-MM-dd。",
            ],
            "query_core_info_v2": [
                "begin_date: 开始日期，格式 yyyy-MM-dd。",
                "end_date: 结束日期，格式 yyyy-MM-dd。",
            ],
        }
        for tool_name, snippets in expectations.items():
            with self.subTest(tool=tool_name):
                self.assert_tool_contains(tool_name, snippets)


if __name__ == "__main__":
    unittest.main()
