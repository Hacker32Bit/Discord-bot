#!/bin/bash

LOGFILE="/tmp/backup.log"

set -e
timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
WORK_DIR="/home/gektor/Discord-bot"
GDRIVE_PATH="gdrive:/Discord-bot"

echo "[INFO] Backup started at $timestamp" | tee -a "$LOGFILE"

# 2. Sync files to Google Drive
echo "[INFO] Backing up files..." | tee -a "$LOGFILE"
echo "Uploading logs..."
if rclone copy "/tmp/logs/" "$GDRIVE_PATH/backups/logs/" --copy-links; then
  echo "Logs uploaded successfully."
else
  echo "Failed to upload logs." >&2
fi

if rclone copyto --ignore-times "$WORK_DIR/database.sqlite" "$GDRIVE_PATH/backups/databases/${timestamp}.sqlite"; then
  echo "Database uploaded successfully."
else
  echo "Failed to upload database." >&2
fi

if rclone copy "$WORK_DIR/assets/images/rank_cards/" "$GDRIVE_PATH/backups/assets/images/rank_cards/" --copy-links; then
  echo "Ranks cards uploaded successfully."
else
  echo "Failed to upload cards." >&2
fi

if rclone copyto "/tmp/terminal_log.log" "$GDRIVE_PATH/backups/terminal_logs/${timestamp}.log"; then
  echo "Terminal log uploaded successfully."
else
  echo "Failed to upload terminal logs." >&2
fi

if [ $? -eq 0 ]; then
    echo "[INFO] Backup complete." | tee -a "$LOGFILE"
else
    echo "[ERROR] Backup failed!" | tee -a "$LOGFILE"
    exit 1
fi

sleep 5

# Reboot or shutdown
ACTION=$(cat /tmp/bot_action 2>/dev/null || echo "none")
echo "$ACTION" | tee -a "$LOGFILE"
if [ "$ACTION" == "reboot" ]; then
  echo "Rebooting system..." | tee -a "$LOGFILE"
  sudo reboot
elif [ "$ACTION" == "shutdown" ]; then
  echo "Shutting down system..." | tee -a "$LOGFILE"
  sudo shutdown -h now
else
  echo "Unknown action: $ACTION" | tee -a "$LOGFILE"
fi