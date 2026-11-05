import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "xvb-lab"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(CONFIG_FILE)
