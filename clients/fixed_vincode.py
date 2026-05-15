from clients.customer_app_config import get_config_value

DEFAULT_FIXED_VINCODE = "XUGG2154CTKA02713"


def get_fixed_vincode() -> str:
    return str(
        get_config_value("fixed_vincode", DEFAULT_FIXED_VINCODE)
        or DEFAULT_FIXED_VINCODE
    ).strip()
