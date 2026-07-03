import csv
import json
from pathlib import Path
from typing import Any


TEXT_COLUMNS = ("text", "tweet_text", "full_text", "content", "comment")
USERNAME_COLUMNS = ("username", "user.username", "author.username", "screen_name", "user")


def read_export_rows(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        with input_path.open(encoding="utf-8") as input_file:
            for line in input_file:
                stripped = line.strip()
                if stripped:
                    value = json.loads(stripped)
                    if isinstance(value, dict):
                        rows.append(value)
        return rows

    if suffix == ".json":
        with input_path.open(encoding="utf-8") as input_file:
            value = json.load(input_file)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            for key in ("data", "results", "tweets", "items"):
                nested = value.get(key)
                if isinstance(nested, list):
                    return [row for row in nested if isinstance(row, dict)]
            return [value]
        return []

    with input_path.open(newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def nested_value(row: dict[str, Any], key: str) -> Any:
    value: Any = row
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def pick_value(row: dict[str, Any], candidates: tuple[str, ...], default: Any = "") -> Any:
    normalized = {str(key).lower(): value for key, value in row.items()}
    for candidate in candidates:
        value = nested_value(row, candidate)
        if value not in (None, ""):
            return value
        value = normalized.get(candidate.lower())
        if value not in (None, ""):
            return value
    return default


def load_tweetclaw_export(input_path: str) -> list[dict[str, str]]:
    comments: list[dict[str, str]] = []
    for row in read_export_rows(Path(input_path)):
        text = " ".join(str(pick_value(row, TEXT_COLUMNS)).split())
        if not text:
            continue
        username = " ".join(str(pick_value(row, USERNAME_COLUMNS, "tweetclaw_export")).split())
        comments.append({"text": text, "username": username or "tweetclaw_export"})
    if not comments:
        raise ValueError("No tweet text rows found in the TweetClaw export.")
    return comments
