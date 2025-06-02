import logging.config
import os
from pathlib import Path

import yaml

from config.settings_config import settings


def deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and key in base:
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def setup_logging():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    base_config_path = os.path.join(base_dir, "config", "logging", "logging.yaml")
    env_config_path = os.path.join(
        base_dir, "config", "logging", f"logging.{settings.env}.yaml"
    )

    with open(base_config_path, "r") as f:
        base_config = yaml.safe_load(f)

    if Path(env_config_path).exists():
        with open(env_config_path, "r") as f:
            override_config = yaml.safe_load(f)
        config = deep_merge(base_config, override_config)
    else:
        config = base_config

    for handler in config.get("handlers", {}).values():
        filename = handler.get("filename")
        if filename:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(config)
