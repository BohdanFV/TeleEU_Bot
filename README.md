# TeleEU Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![Google Sheets](https://img.shields.io/badge/Data-Google%20Sheets-34A853)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

**TeleEU Bot** is a Telegram bot for working with university class schedules. It helps students register their group, receive automatic Telegram reminders before lessons, view schedules for today/tomorrow/week, and open online class links directly from the bot.

The project is designed as a production-style Python application: configuration is stored in environment variables, runtime data is separated from source code, the bot is split into modules, and the repository is ready for local launch or Linux server deployment.

---

## Key features

- **Telegram schedule assistant** — students can register their education form, faculty, course and group through Telegram buttons.
- **Automatic lesson notifications** — the bot checks lesson time and sends Telegram reminders before classes.
- **Schedule commands** — quick access to today’s, tomorrow’s and weekly schedule.
- **Google Sheets data parsing** — schedule data is loaded from Google Sheets/API sources and normalized for bot usage.
- **Human-input parsing** — the project processes imperfect human-entered data in spreadsheets: lesson types, group numbers, dates, teacher names and online meeting links.
- **Online class link detection** — the bot determines whether a lesson should use Zoom/Google Meet-style links based on configured keywords and parsed schedule fields.
- **SQLite persistence** — user registrations and bot state are stored locally in a SQLite database.
- **Background worker** — notification logic runs alongside Telegram polling.
- **Configurable runtime** — tokens, API keys, paths, retry intervals, test mode and polling options are controlled through `.env`.
- **Linux service support** — includes a `systemd` service example for running the bot continuously on a server.
- **Testable helper logic** — parsing utilities are covered with unit tests.

---

## Technology stack

| Area | Technologies / skills |
|---|---|
| Language | Python 3.11+ |
| Telegram integration | `pyTelegramBotAPI`, Telegram Bot API, inline/reply keyboards, callbacks |
| External data | Google Sheets API, JSON schedule caches, HTTP requests |
| Data processing | parsing, normalization, date handling, group matching, lesson-type detection |
| Storage | SQLite |
| Configuration | `.env`, `python-dotenv`, typed settings dataclass |
| Runtime | background threads, retry logic, polling restart handling |
| Deployment | Windows PowerShell, Linux shell, `systemd` |
| Quality | modular package structure, tests with `pytest`, GitHub Actions workflow, `.gitignore`, clean repository layout |

---

## How the bot works

1. A student starts the bot and registers their education form, faculty, course and subgroup.
2. The bot builds the student group identifier and saves the registration in SQLite.
3. Schedule data is read from local JSON cache files and can be updated from external Google Sheets/API sources.
4. The parser normalizes spreadsheet data that may be entered manually by people: dates, groups, lesson names, lesson types, teachers and class links.
5. The background notification worker checks upcoming lessons and sends Telegram reminders before the configured time.
6. The student can request schedule information or class access links directly from Telegram commands and buttons.

---

## Project structure

```text
TeleEU_Bot/
├── data/
│   ├── faculties/              # Faculty configuration cache
│   ├── links/                  # Online class links cache
│   └── schedules/              # Schedule JSON cache files
├── docs/
│   └── DEPLOYMENT.md           # Additional Linux deployment notes
├── logs/
│   └── .gitkeep                # Runtime logs are ignored by Git
├── scripts/
│   ├── run.sh                  # Linux/macOS helper runner
│   └── run_windows.ps1         # Windows PowerShell helper runner
├── src/
│   └── teleeu_bot/
│       ├── app.py              # Application bootstrap and worker startup
│       ├── config.py           # Environment-based settings
│       ├── database.py         # SQLite access layer
│       ├── keyboards.py        # Telegram keyboard builders
│       ├── logging_config.py   # File/console logging setup
│       ├── models.py           # Domain data structures
│       ├── handlers/           # Telegram commands and callbacks
│       ├── services/           # Schedule, links and notifications logic
│       └── utils/              # Parsing, date and Telegram helpers
├── systemd/
│   └── teleeu-bot.service.example
├── tests/
│   ├── test_config.py
│   └── test_parsing.py
├── .github/workflows/        # Automated test workflow
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Requirements

- Python **3.11+**
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Google API key if schedule updates from Google Sheets/API are enabled
- Windows 10/11 or Linux server/desktop

---

## Environment configuration

Create a private `.env` file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Minimum required values:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BOT_USERNAME=@your_bot_username
GOOGLE_API_KEY=your_google_api_key
```

The `.env` file is private and must not be committed to GitHub. The repository already ignores it through `.gitignore`.

Important configuration groups:

| Group | Variables |
|---|---|
| Telegram | `TELEGRAM_BOT_TOKEN`, `BOT_USERNAME`, `TEST_TELEGRAM_BOT_TOKEN`, `TEST_BOT_USERNAME` |
| Google/API | `GOOGLE_API_KEY`, `GOOGLE_SHEETS_API_BASE_URL`, `LINKS_SOURCE_URL`, `FACULTIES_SOURCE_URL` |
| Paths | `DATABASE_PATH`, `TEST_DATABASE_PATH`, `DATA_DIR`, `LOGS_DIR` |
| Notifications | `NOTIFY_BEFORE_MINUTES`, `TEST_NOTIFY_BEFORE_MINUTES`, `NOTIFICATION_ATTEMPTS`, `NOTIFICATION_RETRY_WINDOW_MINUTES` |
| Schedule updates | `UPDATE_SCHEDULE_EVERY_DAY`, `UPDATE_LINKS_ENABLED`, `SCHEDULE_ATTEMPTS`, `SCHEDULE_ATTEMPT_PAUSE` |
| Academic logic | `MONTH_OF_COURSE_CHANGE`, `DAY_OF_COURSE_CHANGE` |
| Telegram polling | `POLLING_TIMEOUT`, `POLLING_RESTART_PAUSE` |
| Parsing | `LESSON_TYPE_KEYWORDS` |
| Logging/debug | `LOG_LEVEL`, `DEBUG_CHAT_ID`, `DEBUG_ERROR_THREAD_ID`, `DEBUG_CRITICAL_THREAD_ID` |

See `.env.example` for the complete list of supported options.

---

## Run on Windows

Open PowerShell in the project folder and run:

```powershell
cd C:\Users\<YourUser>\Desktop\TeleEU_Bot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
```

Fill `.env` with your real Telegram and Google values, then start the bot:

```powershell
python -m teleeu_bot
```

Alternative command after editable installation:

```powershell
teleeu-bot
```

Helper script:

```powershell
.\scripts\run_windows.ps1
```

If PowerShell blocks virtual environment activation, allow scripts for the current user:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Run on Linux

```bash
git clone https://github.com/<your-username>/TeleEU_Bot.git
cd TeleEU_Bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
nano .env
python -m teleeu_bot
```

Helper script:

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

---

## Run as a Linux systemd service

A `systemd` service lets the bot run continuously in the background and restart after failures or server reboot.

### 1. Copy the project to `/opt`

```bash
sudo mkdir -p /opt/TeleEU_Bot
sudo cp -r . /opt/TeleEU_Bot
cd /opt/TeleEU_Bot
```

### 2. Create virtual environment and install the project

```bash
sudo python3 -m venv .venv
sudo .venv/bin/python -m pip install --upgrade pip
sudo .venv/bin/python -m pip install -e .
```

### 3. Create and fill `.env`

```bash
sudo cp .env.example .env
sudo nano .env
```

### 4. Create a service user

```bash
sudo useradd --system --home /opt/TeleEU_Bot --shell /usr/sbin/nologin teleeu || true
sudo chown -R teleeu:teleeu /opt/TeleEU_Bot
```

### 5. Install the service file

```bash
sudo cp systemd/teleeu-bot.service.example /etc/systemd/system/teleeu-bot.service
sudo nano /etc/systemd/system/teleeu-bot.service
```

Check that paths and user match your server:

```ini
WorkingDirectory=/opt/TeleEU_Bot
EnvironmentFile=/opt/TeleEU_Bot/.env
ExecStart=/opt/TeleEU_Bot/.venv/bin/python -m teleeu_bot
User=teleeu
```

### 6. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable teleeu-bot
sudo systemctl start teleeu-bot
sudo systemctl status teleeu-bot
```

View logs:

```bash
journalctl -u teleeu-bot -f
```

Restart after changing `.env` or code:

```bash
sudo systemctl restart teleeu-bot
```

Stop the service:

```bash
sudo systemctl stop teleeu-bot
```

---

## Bot commands

| Command | Purpose |
|---|---|
| `/start` | Start registration and open the main menu |
| `/Коди доступу` | Open access codes/resources |
| `/Налаштування` | Change user settings |
| `/Розклад на сьогодні` | Show today’s schedule |
| `/Розклад на завтра` | Show tomorrow’s schedule |
| `/Розклад на цей тиждень` | Show weekly schedule |
| `/next_lessons` | Show upcoming lessons |
| `/ping` | Show current bot time |
| `/status` | Show runtime status |

---

## Tests and CI

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests locally:

```bash
pytest
```

Or without installing the package:

```bash
PYTHONPATH=src pytest
```

Windows PowerShell variant:

```powershell
$env:PYTHONPATH="src"
pytest
```

The repository also includes a GitHub Actions workflow in `.github/workflows/tests.yml` for automatic test execution on push and pull requests.

---

## Security checklist before publishing

Before pushing the repository to GitHub:

- keep `.env` local only;
- do not commit Telegram tokens or Google API keys;
- do not commit SQLite databases with real users;
- do not commit runtime logs;
- check `git status` before every commit;
- use `.env.example` for public configuration documentation.

Useful check:

```bash
git status --short
```

---

## License

This project is distributed under the MIT License. See `LICENSE` for details.

---

## Repository purpose

This repository demonstrates a complete Telegram bot application with real schedule-processing logic, Google Sheets data integration, human-entered data parsing, SQLite persistence, background notifications, environment-based configuration, tests and Linux deployment support.
