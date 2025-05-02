#!/bin/bash

set -e
timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
WORK_DIR="/home/gektor/Discord-bot"
GDRIVE_PATH="gdrive:/Discord-bot"
PYTHON_PID_FILE="/tmp/discord_bot.pid"

# 1. Stop bot
if [ -f "$PYTHON_PID_FILE" ]; then
  kill -SIGINT $(cat "$PYTHON_PID_FILE")
  rm "$PYTHON_PID_FILE"
  sleep 10
fi

# 2. Sync files to Google Drive
rclone copy "/tmp/logs/" "$GDRIVE_PATH/backups/logs/"
rclone copy "$WORK_DIR/assets/images/rank_cards/" "$GDRIVE_PATH/backups/assets/images/rank_cards/"
rclone copyto "/tmp/terminal_log.log" "$GDRIVE_PATH/backups/terminal_logs/${timestamp}.log"
rclone copyto "$WORK_DIR/database.sqlite" "$GDRIVE_PATH/backups/databases/${timestamp}.sqlite"

# 3. Optional: wait for rclone to complete syncs
sleep 30

# 4. Reboot
sudo reboot