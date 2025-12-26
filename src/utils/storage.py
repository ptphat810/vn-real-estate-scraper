import json
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("data")

def save_data(properties_data):
    if not properties_data:
        return

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"data/raw/bds_{date_str}.json"

    existing_data = []

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            logger.warning(f"Could not read {filename}, starting fresh.")
            existing_data = []

    existing_data.extend(properties_data)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved {filename} with {len(properties_data)} new records.")
    except Exception as e:
        logger.error(f"Error saving to {filename}: {e}")