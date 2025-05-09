# Discord-bot
Bot for discord server "The lair of Hacker32Bit"

1. Clone.
2. Setup venv with ".venv" name
3. Install requirements.txt
4. Move database.sqlite and .env file to your folder(If exist, if not exist create .env)
```
DISCORD_TOKEN = MTI0MD...gbi74U
...
...
...
```
5. Setup systemd .service. (/etc/systemd/system/discord-bot.service)
```
[Service]
Type=simple
User=gektor
WorkingDirectory=/home/gektor/Discord-bot

# Kill old processes
ExecStartPre=/usr/bin/bash -c '/usr/bin/pkill -u gektor -f "/home/gektor/Discord-bot/main.py" || true'
ExecStartPre=/home/gektor/Discord-bot/scripts/restore.sh

ExecStart=/home/gektor/Discord-bot/.venv/bin/python /home/gektor/Discord-bot/main.py
ExecStopPost=/home/gektor/Discord-bot/scripts/backup.sh

# Let systemd handle reconnects, but prevent fast restart loops
Restart=on-failure
RestartSec=10

Environment=PYTHONUNBUFFERED=1
Environment=VIRTUAL_ENV=/home/gektor/Discord-bot/.venv
Environment=PATH=/home/gektor/Discord-bot/.venv/bin:/usr/bin:/bin

StandardOutput=append:/tmp/terminal_log.log
StandardError=append:/tmp/terminal_log.log
```