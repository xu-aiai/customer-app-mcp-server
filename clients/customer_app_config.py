import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "customer_app_config.json"


def load_customer_app_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_customer_app_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)
        config_file.write("\n")


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    return load_customer_app_config().get(key, default)


def get_customer_app_token() -> Optional[str]:
    token = load_customer_app_config().get("token")
    return token or None


def update_customer_app_token(token: str) -> None:
    config = load_customer_app_config()
    config["token"] = token
    save_customer_app_config(config)
