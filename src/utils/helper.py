import yaml
import os
import json
from datetime import datetime


def load_config(config_path="src/config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Not found config: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def save_json(data):
    if not data:
        return

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"data/raw/posts_{date_str}.json"
    existing_data = []

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            existing_data = []

    existing_data.extend(data)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(e)
