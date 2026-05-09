# Customer App MCP Server | 客户 App MCP 服务

An MCP server for querying customer app vehicle data, work-hour statistics, traces, faults, maintenance plans, and related business APIs.

一个用于查询客户 App 车辆数据、工时统计、轨迹、故障、维保计划等业务接口的 MCP 服务。

## Overview | 概述

MCP (Model Context Protocol) is a protocol that allows servers to expose tools that can be invoked by language models. Tools enable models to interact with external systems, such as querying databases, calling APIs, or performing computations. Each tool is uniquely identified by a name and includes metadata describing its schema.

MCP（模型上下文协议）是一个允许服务器向语言模型暴露可调用工具的协议。这些工具使模型能够与外部系统交互，例如查询数据库、调用API或执行计算。每个工具都由一个唯一的名称标识，并包含描述其模式的元数据。

## Features | 特性

- Vehicle and device lookup by vincode | 按设备编码/车架号查询车辆设备
- Configurable telematics provider switch (domestic/overseas) | 支持国内/海外车联网切换
- Work-hour statistics and daily details | 工时汇总和按日明细查询
- Trace, condition, fault, and maintenance queries | 轨迹、工况、故障、维保查询
- Fault repair preparation and CRM+ repair order submission | 故障报修信息准备与 CRM+ 维修工单提交
- WebSocket bridge for Xiaozhi MCP endpoint | 对接小智 MCP 接入点的 WebSocket 管道

## Quick Start | 快速开始

1. Install dependencies | 安装依赖:
```bash
pip install -r requirements.txt
```

2. Set up MCP endpoint | 设置 MCP 接入点:

Edit `mcp_config.json` and replace `mcpEndpoint` with the MCP endpoint copied from your Xiaozhi console.

编辑 `mcp_config.json`，将 `mcpEndpoint` 替换为你在小智控制台智能体里复制的 MCP 接入点地址。

3. Run the MCP pipe | 启动 MCP 管道:
```bash
conda run --no-capture-output -n customer-app-mcp-server python mcp_pipe.py
```

The command above starts all enabled servers in `mcp_config.json`. `--no-capture-output` keeps logs visible while the process is running.

上面的命令会启动 `mcp_config.json` 中所有启用的服务。`--no-capture-output` 可以让运行日志实时显示。

You can also run the server script directly:

也可以直接指定服务脚本启动：
```bash
conda run --no-capture-output -n customer-app-mcp-server python mcp_pipe.py mcp_server.py
```

Usually you do not need to pass `mcp_server.py`; running `mcp_pipe.py` is enough because `mcp_config.json` already defines the server command.

通常不需要再指定 `mcp_server.py`；直接运行 `mcp_pipe.py` 即可，因为 `mcp_config.json` 已经定义了服务启动命令。

*Requires `mcp_config.json` configuration file with server definitions (supports stdio/sse/http transport types)*

*需要 `mcp_config.json` 配置文件定义服务器（支持 stdio/sse/http 传输类型）*

## Project Structure | 项目结构

- `mcp_pipe.py`: Main communication pipe that handles WebSocket connections and process management | 处理WebSocket连接和进程管理的主通信管道
- `mcp_server.py`: MCP server entrypoint and tool registration | MCP 服务入口和工具注册
- `tools/`: MCP tool adapters and tool-level validation | MCP 工具适配层和工具入参校验
- `clients/`: External API clients and shared request helpers | 外部接口客户端和公共请求方法
- `requirements.txt`: Project dependencies | 项目依赖

## Customer App API Config | 客户 App 接口配置

客户 App 接口配置存放在 `config/customer_app_config.json`：

- `telematics_provider`: 车联网桥接选择，支持 `domestic` / `overseas`，默认 `domestic`
- `domestic_telematics.base_url`: 国内车联网桥接地址
- `domestic_telematics.app_id` / `domestic_telematics.app_secret`: 国内车联网签名鉴权凭据
- `api_base_url`: 业务接口 base URL
- `service_order_base_url`: 工单接口 base URL，对应 `XCMG_SERVICE_ORDER_BASE_URL`
- `service_base_url`: 保养&报修统一工单接口 base URL
- `auth_base_url`: 登录接口 base URL
- `language`: 请求语言
- `auth.username` / `auth.password`: 获取登录 token 所需账号密码
- `auth.authorization`: 获取登录 token 所需 Basic Authorization
- `token`: 业务接口使用的 Bearer token

Apifox 开发环境默认地址：

```json
{
  "telematics_provider": "domestic",
  "domestic_telematics": {
    "base_url": "https://machinery360.hanyunmmip.cn",
    "app_id": "",
    "app_secret": ""
  },
  "api_base_url": "http://10.90.21.125:9085/business",
  "service_order_base_url": "http://10.90.21.125:9085",
  "service_base_url": "http://10.90.21.125:9085/ixcmg",
  "auth_base_url": "http://10.90.21.125:9085/auth"
}
```

登录 token 请求路径：

```text
POST http://10.90.21.125:9085/auth/oauth/token
```

当 `telematics_provider=domestic` 时，MCP 车联网工具会走国内车联网桥接，启动时不会再自动刷新海外客户 App token。

当前国内车联网已单独接入的能力：

- `query_vehicle_by_vincode`
- `query_vehicle_by_vincode_v2`
- `query_planned_maintained_item_page`
- `query_planned_maintained_item_page_v2`
- `get_customer_condition`
- `query_trace`
- `query_trace_v2`
- `query_work_hours_statistic_info_by_vehicle`
- `query_work_hours_statistic_info_by_vehicle_v2`
- `query_work_hours_page_new_by_date`
- `query_work_hours_page_new_by_date_v2`
- `query_core_info`
- `query_core_info_v2`
- `query_customer_vehicle_page`
- `query_customer_vehicle_page_v2`
- `query_work_rate`
- `get_work_condition_header`
- `get_current_work_condition`
- `query_history_work_condition`
- `get_env_pro_data`
- `query_env_pro_history_data`
- `query_vehicle_alarm`
- `query_indicator_data`
- `query_tags_data`

国内与海外的 client 和接口协议已分开实现：

- 海外继续走原 `customer_app` 体系
- 国内走独立 `domestic_telematics` 体系
- 国内模式默认固定查询预置 VIN
- 海外模式保留按入参查询单台或多台设备的能力

其中 `query_customer_vehicle_page` 会退化为基于 `getBaseInfo` 的单车/批量档案封装分页结果。暂未提供国内文档的接口在 `domestic` 模式下会直接返回“暂不支持”。

获取并写入 token：

```bash
conda run -n customer-app-mcp-server python scripts/fetch_customer_app_token.py
```

服务启动时会在鉴权配置完整的情况下自动获取客户 App token，并写回 `config/customer_app_config.json` 的 `token` 字段。调用业务接口时，如果返回 401/403 或 token 失效类错误，客户端会自动重新获取 token、写回配置文件，并用新 token 重试本次业务请求一次。

## Fault Repair Tools | 故障报修工具

故障报修拆分为两个 MCP tools：

- `prepare_fault_repair`: 负责报修信息准备，不创建 CRM 工单。车机报修场景下整机编码固定为当前设备，不询问用户报修哪台设备；工具会合并已抽取字段和会话状态，查询当前设备详情，信息齐全后返回 `submitWorkorder` payload。返回结果包含可直接播报的 `response` 字段。
- `submit_fault_repair_order`: 用户确认后调用 CRM+ 创建维修服务单。可直接传入 `prepare_fault_repair` 返回的 `submit_payload`，也可传入拆分字段。

`submit_fault_repair_order` 的 CRM+ 配置从 `config/customer_app_config.json` 读取：

```json
{
  "crmplus_base_url": "https://app-crmplus-uat.xcmg.com",
  "crmplus_app_id": "...",
  "crmplus_app_secret": "..."
}
```

核心字段映射：

```json
{
  "deviceVin": "new_userprofile_code",
  "faultDescription": "new_memo",
  "contactName": "new_contact",
  "contactPhone": "new_feedbacktel",
  "detailAddress": "new_address"
}
```

## Service Order Tools | 工单查询工具

已有工单/服务单查询拆分为两个 MCP tools：

- `list_service_orders`: 查询当前用户最近工单列表，默认取最近 3 条。可传 `vincode` 按设备 VIN 过滤。
- `get_service_order_detail`: 查询单条工单详情，传入 `order_id`。

这两个工具用于“我的工单到哪了”“服务单进度”“上次报修怎么样了”“查工单详情”等查询已有工单的场景；新建报修仍使用 `prepare_fault_repair` / `submit_fault_repair_order`。

接口路径：

```text
GET {service_order_base_url}/ixcmg/serviceOrderUnion/getPage
GET {service_order_base_url}/ixcmg/serviceOrderUnion/{order_id}
```

默认完整接口路径：

```text
http://10.90.21.125:9085/ixcmg/serviceOrderUnion/getPage
http://10.90.21.125:9085/ixcmg/serviceOrderUnion/{order_id}
```

入参示例：

```json
{
  "app_token": "可选，用户客户 App token；不传时使用 config/customer_app_config.json 的 token",
  "vincode": "可选设备 VIN",
  "page_num": 1,
  "page_size": 3
}
```

Token 使用边界：

- 工单查询走客户 App token，即 `app_token` / `xcmg_app_token`，未传时使用 `config/customer_app_config.json` 的 `token` 并按客户 App 逻辑自动刷新。
- CRM+ token 只由 `submit_fault_repair_order` 内部通过 CRM+ `/token` 获取，用于 `POST /api/service/CreateWorkOrder`，不会传给工单查询接口。

工具只返回压缩后的结构化事实数据和中文枚举标签，不做 LLM 总结。

## Apifox API Coverage | Apifox 接口覆盖

MCP 已覆盖 Apifox 文档中的 AI 团队接口 v1/v2：

- `/apiForAi/*`
- `/apiForAi/v2/*`

保养&报修统一工单接口通过通用工具 `call_service_order_union` 调用：

```json
{
  "endpoint": "add",
  "method": "POST",
  "payload": {}
}
```

`endpoint` 可以传 `getPage`、`listByUser`、`homePage`、`add`、`getDevice`、`getDeviceSrvOrder`、`getAllDeviceSrvOrder` 等，也可以传完整路径 `/serviceOrderUnion/add`。

## Config-driven Servers | 通过配置驱动的服务

编辑 `mcp_config.json` 文件来配置服务器列表（也可设置 `MCP_CONFIG` 环境变量指向其他配置文件）。

配置说明：
- 无参数时启动所有配置的服务（自动跳过 `disabled: true` 的条目）
- 有参数时运行单个本地脚本文件
- `type=stdio` 直接启动；`type=sse/http` 通过 `python -m mcp_proxy` 代理

## Creating MCP Tools | 创建 MCP 工具

Here's a simple example of creating an MCP tool | 以下是一个创建MCP工具的简单示例:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("YourToolName")

@mcp.tool()
def your_tool(parameter: str) -> dict:
    """Tool description here"""
    # Your implementation
    return {"success": True, "result": result}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Use Cases | 使用场景

- Mathematical calculations | 数学计算
- Email operations | 邮件操作
- Knowledge base search | 知识库搜索
- Remote device control | 远程设备控制
- Data processing | 数据处理
- Custom tool integration | 自定义工具集成

## Requirements | 环境要求

- Python 3.7+
- websockets>=11.0.3
- python-dotenv>=1.0.0
- mcp>=1.8.1
- pydantic>=2.11.4
- mcp-proxy>=0.8.2

## Contributing | 贡献指南

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献代码！请随时提交Pull Request。

## License | 许可证

This project is licensed under the MIT License - see the LICENSE file for details.

本项目采用MIT许可证 - 详情请查看LICENSE文件。

## Acknowledgments | 致谢

- Thanks to all contributors who have helped shape this project | 感谢所有帮助塑造这个项目的贡献者
- Inspired by the need for extensible AI capabilities | 灵感来源于对可扩展AI能力的需求
