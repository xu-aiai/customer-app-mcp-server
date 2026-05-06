import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from clients.customer_app_auth import fetch_customer_app_token  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("FETCH_CUSTOMER_APP_TOKEN")


if __name__ == "__main__":
    try:
        fetch_customer_app_token()
    except Exception as exc:
        logger.error("Failed to fetch customer app token: %s", exc)
        sys.exit(1)
