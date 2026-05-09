from typing import Optional

from clients.customer_app import CustomerAppClient, REQUEST_TIMEOUT_SECONDS
from clients.customer_app_config import get_config_value
from clients.domestic_telematics import DomesticTelematicsClient

DOMESTIC_PROVIDER = "domestic"
OVERSEAS_PROVIDER = "overseas"


def get_telematics_provider() -> str:
    provider = str(
        get_config_value("telematics_provider", DOMESTIC_PROVIDER)
        or DOMESTIC_PROVIDER
    ).strip().lower()
    if provider not in {DOMESTIC_PROVIDER, OVERSEAS_PROVIDER}:
        return DOMESTIC_PROVIDER
    return provider


def create_telematics_client(
    base_url: Optional[str] = None,
    service_base_url: Optional[str] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
):
    if get_telematics_provider() == DOMESTIC_PROVIDER:
        return DomesticTelematicsClient(
            base_url=base_url,
            service_base_url=service_base_url,
            timeout=timeout,
        )
    return CustomerAppClient(
        base_url=base_url,
        service_base_url=service_base_url,
        timeout=timeout,
    )
