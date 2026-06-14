"""Entrypoint: load configs, register cron jobs, start the scheduler."""

from __future__ import annotations

import logging
import os
import sys
from itertools import cycle

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from src.config import Check, load_configs
from src.notifier import format_message, send
from src.runner import run_curl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def make_job(check: Check, token: str, chat_id: str):
    proxy_cycle = cycle(check.proxies or []) if check.proxies else None

    def job():
        logger.info("Running check '%s'", check.name)
        proxy = next(proxy_cycle) if proxy_cycle else None
        if proxy:
            logger.info("Using proxy for '%s': %s", check.name, proxy)
        result = run_curl(check.curl, proxy=proxy)
        text = format_message(check.description, result.as_text())
        send(token, chat_id, text)
        logger.info("Sent result for '%s' (exit %d)", check.name, result.returncode)

    job.__name__ = check.name
    return job


def main() -> None:
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set — aborting")
        sys.exit(1)

    default_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    config_dir = os.environ.get("CONFIG_DIR", "configs")

    checks = load_configs(config_dir)
    if not checks:
        logger.error("No valid configs loaded from '%s' — aborting", config_dir)
        sys.exit(1)

    scheduler = BlockingScheduler()

    for check in checks:
        chat_id = check.chat_id or default_chat_id
        if not chat_id:
            logger.error(
                "Skipping '%s': no chat_id in config and TELEGRAM_CHAT_ID not set",
                check.name,
            )
            continue

        try:
            trigger = CronTrigger.from_crontab(check.schedule)
        except ValueError as exc:
            logger.error("Skipping '%s': bad cron expression '%s': %s", check.name, check.schedule, exc)
            continue

        scheduler.add_job(
            make_job(check, token, chat_id),
            trigger=trigger,
            id=check.name,
            name=check.description,
            misfire_grace_time=60,
        )
        logger.info("Registered job '%s' — schedule: %s — chat: %s", check.name, check.schedule, chat_id)

    if not scheduler.get_jobs():
        logger.error("No jobs registered — aborting")
        sys.exit(1)

    logger.info("Starting scheduler with %d job(s)", len(scheduler.get_jobs()))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
