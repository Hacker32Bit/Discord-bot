#!/bin/bash

set -e
export PATH="/home/gektor/Discord-bot/.venv/bin:$PATH"
WORK_DIR="/home/gektor/Discord-bot"
GDRIVE_PATH="gdrive:/Discord-bot"
LOG_FILE="/tmp/terminal_logs/$(date '+%Y-%m-%d %H:%M:%S').log"
PYTHON="$WORK_DIR/.venv/bin/python"

# 1. Wait for Internet (retry until ping works)
until ping -c1 8.8.8.8 &>/dev/null; do
  echo "Waiting for Internet..."
  sleep 10
done

# 2. Update project
cd $WORK_DIR
git pull

# 3. Upgrade dependencies
. $WORK_DIR/.venv/bin/activate
pip install -U g4f
PYTHON_SITE_PACKAGES=$(find "$VIRTUAL_ENV/lib" -type d -name "site-packages" | head -n 1)
rsync -rcv "$WORK_DIR/files_for_copy/" "$PYTHON_SITE_PACKAGES/"

# 4. Check Google Drive (assumes rclone is already mounted or accessible)
if ! rclone lsf gdrive: &>/dev/null; then
  echo "Google Drive unavailable!"
  exit 1
fi

# 5. Restore backups
rclone move "$GDRIVE_PATH/database.sqlite" "$WORK_DIR/"
rclone copy "$GDRIVE_PATH/.env" "$WORK_DIR/"
rclone copy "$GDRIVE_PATH/backups/assets/" "$WORK_DIR/assets/" --copy-links --recursive

# 6. Start main.py with logging
mkdir -p /tmp/terminal_logs
$PYTHON main.py >> "$LOG_FILE" 2>&1 &
echo $! > /tmp/discord_bot.pid