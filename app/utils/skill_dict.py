import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "skills_dict.json"


def load_skill_dict() -> dict[str, list[str]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)