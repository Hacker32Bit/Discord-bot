#!/bin/bash

MODE=$1

set -e
timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
WORK_DIR="/home/gektor/Discord-bot"
GDRIVE_PATH="gdrive:/Discord-bot"
PYTHON_PID_FILE="/tmp/discord_bot.pid"

# 1. Stop bot
systemctl stop discord-bot.service
# Graceful shutdown
#if [ -f /tmp/discord_bot.pid ]; then
#    BOT_PID=$(cat /tmp/discord_bot.pid)
#    echo "Stopping bot (PID: $BOT_PID)..."
#    kill -SIGINT "$BOT_PID"
#    sleep 10
#else
#    echo "No PID file found. Trying pgrep fallback..."
#    BOT_PID=$(pgrep -f "main.py")
#    if [ -n "$BOT_PID" ]; then
#        kill -SIGINT "$BOT_PID"
#        sleep 10
#    else
#        echo "Bot not running."
#    fi
#fi

# 2. Sync files to Google Drive
echo "Uploading logs..."
if rclone copy "/tmp/logs/" "$GDRIVE_PATH/backups/logs/" --copy-links; then
  echo "Logs uploaded successfully."
else
  echo "Failed to upload logs." >&2
fi

if rclone copy "$WORK_DIR/assets/images/rank_cards/" "$GDRIVE_PATH/backups/assets/images/rank_cards/"; then
  echo "cards uploaded successfully."
else
  echo "Failed to upload cards." >&2
fi

if rclone copyto "/tmp/terminal_log.log" "$GDRIVE_PATH/backups/terminal_logs/${timestamp}.log"; then
  echo "Terminal logs uploaded successfully."
else
  echo "Failed to upload terminal logs." >&2
fi

if rclone copyto "$WORK_DIR/database.sqlite" "$GDRIVE_PATH/backups/databases/${timestamp}.sqlite"; then
  echo "Database uploaded successfully."
else
  echo "Failed to upload database." >&2
fi

# Now reboot or shutdown
if [[ "$MODE" == "shutdown" ]]; then
    echo "[INFO] Shutting down system..."
    sudo shutdown -h now
elif [[ "$MODE" == "reboot" ]]; then
    echo "[INFO] Rebooting system..."
    sudo reboot
else
    echo "[ERROR] Unknown mode: $MODE"
    exit 1
fi