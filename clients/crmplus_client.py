from typing import Any, Dict

from clients.crmplus import CRMPlusClient


def create_repair_order(
    contact: str,
    feedback_tel: str,
    userprofile_code: str,
    memo: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a CRM+ repair work order.

    This compatibility module mirrors the latest app utility name so MCP tools
    can reuse the same conceptual entrypoint without importing the app package.
    """
    return CRMPlusClient().create_repair_order(
        contact=contact,
        feedback_tel=feedback_tel,
        userprofile_code=userprofile_code,
        memo=memo,
        **kwargs,
    )

