"""Load and validate JSON check configs from a folder."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ("description", "curl", "schedule")


@dataclass
class Check:
    """A single periodic check loaded from a JSON config file."""

    name: str  # source file stem, used for logging / job ids
    description: str
    curl: str
    schedule: str  # 5-field cron expression
    chat_id: str | None = None  # optional per-config override
    proxies: list[str] | None = None  # optional proxy pool


def load_configs(config_dir: str | Path) -> list[Check]:
    """Read every ``*.json`` file in ``config_dir`` into a list of Checks.

    Invalid files are logged and skipped so one bad config never stops the
    service from starting.
    """
    directory = Path(config_dir)
    if not directory.is_dir():
        logger.error("Config directory %s does not exist", directory)
        return []

    checks: list[Check] = []
    for path in sorted(directory.glob("*.json")):
        check = _load_one(path)
        if check is not None:
            checks.append(check)

    if not checks:
        logger.warning("No valid configs found in %s", directory)
    return checks


def _load_one(path: Path) -> Check | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Skipping %s: cannot read/parse (%s)", path.name, exc)
        return None

    if not isinstance(data, dict):
        logger.error("Skipping %s: top-level JSON must be an object", path.name)
        return None

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        logger.error("Skipping %s: missing required field(s): %s", path.name, ", ".join(missing))
        return None

    chat_id = data.get("chat_id")
    raw_proxies = data.get("proxies", [])
    if raw_proxies is None:
        raw_proxies = []
    if not isinstance(raw_proxies, list):
        logger.error("Skipping %s: 'proxies' must be an array of strings", path.name)
        return None

    proxies: list[str] = []
    for idx, value in enumerate(raw_proxies):
        if not isinstance(value, str) or not value.strip():
            logger.error("Skipping %s: proxies[%d] must be a non-empty string", path.name, idx)
            return None
        proxies.append(value.strip())

    return Check(
        name=path.stem,
        description=str(data["description"]),
        curl=str(data["curl"]),
        schedule=str(data["schedule"]),
        chat_id=str(chat_id) if chat_id is not None else None,
        proxies=proxies,
    )
