# tg-req-repeater

Periodically runs HTTP requests and forwards the responses to a Telegram bot. Designed for regularly checking ticket availability by IP or place.

## Quick start

```bash
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
docker compose up --build
```

## Config files

Drop JSON files into `configs/`. Each file is one scheduled check:

```json
{
  "description": "Check site tickets",
  "curl": "curl -sS https://example.com/api/tickets",
  "schedule": "*/5 * * * *",
  "chat_id": "123456789",
  "proxies": ["http://user:pass@127.0.0.1:8080", "socks5://127.0.0.1:9050"]
}
```

| Field | Required | Description |
|---|---|---|
| `description` | yes | Label shown in the Telegram message |
| `curl` | yes | Full curl command to execute |
| `schedule` | yes | 5-field cron expression |
| `chat_id` | no | Telegram chat ID; falls back to `TELEGRAM_CHAT_ID` in `.env` |
| `proxies` | no | Array of proxy URLs. If set, requests use proxies in round-robin order |

The `configs/` folder is mounted as a volume — you can add/edit/remove files and restart the container without rebuilding the image.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | no* | Default chat to send results to |
| `CONFIG_DIR` | no | Path to configs folder (default: `configs`) |
| `TZ` | no | Timezone for cron schedules (default: UTC) |

*Required if any config file omits `chat_id`.

## Running locally (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in token + chat id
python -m src.main
```
