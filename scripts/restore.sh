#!/bin/bash

set -e
export PATH="/home/gektor/Discord-bot/.venv/bin:$PATH"
WORK_DIR="/home/gektor/Discord-bot"
GDRIVE_PATH="gdrive:/Discord-bot"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 1. Wait for Internet (retry until ping works)
until ping -c1 8.8.8.8 &>/dev/null; do
  echo "Waiting for Internet..."
  sleep 10
done

# 2. Update project
cd "$WORK_DIR"

{
    timeout 20s git pull
} || {
    echo "[WARNING] git pull failed or timed out. Continuing anyway."
}

# 3. Upgrade dependencies
source "$WORK_DIR/.venv/bin/activate"
pip install -U g4f
PYTHON_SITE_PACKAGES=$(find "$VIRTUAL_ENV/lib" -type d -name "site-packages" | head -n 1)
rsync -rcv "$WORK_DIR/files_for_copy/" "$PYTHON_SITE_PACKAGES/"

# 4. Check Google Drive (assumes rclone is already mounted or accessible)
if ! rclone lsf gdrive: &>/dev/null; then
  echo "Google Drive unavailable!"
fi

# 5. Restore backups
if rclone lsf "$GDRIVE_PATH" | grep -q "^database.sqlite$"; then
    echo "Found database.sqlite on Google Drive, restoring..."
    rclone move "$GDRIVE_PATH/database.sqlite" "$WORK_DIR/"
else
    echo "No database.sqlite found on Google Drive — skipping restore."
fi
if rclone lsf "$GDRIVE_PATH" | grep -q "^chats.sqlite$"; then
    echo "Found chats.sqlite on Google Drive, restoring..."
    rclone move "$GDRIVE_PATH/chats.sqlite" "$WORK_DIR/"
else
    echo "No chats.sqlite found on Google Drive — skipping restore."
fi
rclone copy "$GDRIVE_PATH/.env" "$WORK_DIR/"
rclone copy "$GDRIVE_PATH/backups/assets/" "$WORK_DIR/assets/" --copy-links

# 6. Start main.py with logging
mkdir -p /tmp/logs