# Deployment notes

This document contains a compact production checklist for running TeleEU Bot on a Linux server.

## Manual Linux launch

```bash
cd /opt/TeleEU_Bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
nano .env
python -m teleeu_bot
```

## systemd launch

```bash
sudo cp systemd/teleeu-bot.service.example /etc/systemd/system/teleeu-bot.service
sudo systemctl daemon-reload
sudo systemctl enable teleeu-bot
sudo systemctl start teleeu-bot
sudo systemctl status teleeu-bot
```

Live logs:

```bash
journalctl -u teleeu-bot -f
```

Restart:

```bash
sudo systemctl restart teleeu-bot
```

Stop:

```bash
sudo systemctl stop teleeu-bot
```

## Production checklist

- `.env` exists on the server and contains real private values.
- `.env` is not committed to GitHub.
- The service file points to the correct `WorkingDirectory` and virtual environment.
- The service user has read/write access to `data/` and `logs/`.
- SQLite database files and logs are kept outside Git commits.
