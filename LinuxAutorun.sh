#!/bin/bash

CURRENT_PID=$$
WORK_DIR=$HOME/Discord-bot
TERMINAL_LOGS_PATH=$WORK_DIR/terminal_logs
DISCORD_LOGS_PATH=$WORK_DIR/logs
PYTHON_PATH=$WORK_DIR/.venv/bin/python
SCRIPT_PATH=$WORK_DIR/main.py
GDRIVE_PATH=$HOME/mnt/gdrive/Discord-bot
RANK_CARDS=$WORK_DIR/assets/images/rank_cards
END_TIME="06:00:00" # Set time when system should be reboot

cd $WORK_DIR


echo() {
  command echo $(date '+%Y-%m-%d %H:%M:%S') "$@"
}

gdrive_check() {
  echo "Checking gdrive availability and access..."
  if test -d $GDRIVE_PATH; then
    echo "gdrive mounted and available!"
  else
    echo "Starting rclone in systemctl..."
    systemctl --user start rclone@gdrive
    echo "Adding loginctl..."
    loginctl enable-linger $USER
    echo "Completed!"

    if test -d $GDRIVE_PATH; then
      echo "gdrive mounted and available!"
    else
      echo "ERROR!"
    fi
  fi

}

connection_check() {
  echo "Checking internet(Google Drive service) availability and waiting for access to network..."

  while ! ping -c 1 -W 1 drive.google.com; do
      echo "Waiting for drive.google.com - network interface might be down..."
      sleep 30
  done
  echo "Connected!"
}

echo "====== Script started! =================================================="

echo "Calculating time..."

sleep_seconds=$(($(date +%s -d $END_TIME)-$(date +%s)))

if [[ ! $sleep_seconds -gt 0 ]]; then
  sleep_seconds=$((86400+$sleep_seconds))
fi

# For debug 10 minutes or 600 seconds
# sleep_seconds=120 # IMPORTANT! dont use small number. It will get in loop of system reboot!

echo "Completed! The script will stopped after $sleep_seconds seconds!"


echo "====== Before start discord.py =========================================="

connection_check

echo "-------------------------------------------------------------------------"

echo "Updating project from GitHub..."
git pull

echo "-------------------------------------------------------------------------"

echo "Updating from gdrive '.env', 'database.sqlite', and 'assets/' if they are different..."
gdrive_check

echo "Checking and updating database.sqlite from gdrive..."
cp -u -v $GDRIVE_PATH/database.sqlite $WORK_DIR/database.sqlite
echo "Checking and updating .env from gdrive..."
cp -u -v $GDRIVE_PATH/.env $WORK_DIR/.env
echo "Checking and updating assets directory from gdrive..."
cp -r -u -v $GDRIVE_PATH/backups/assets/. $WORK_DIR/assets/
echo "Completed!"


echo "====== Starting discord.py script ======================================="

# Run python script using python venv
echo "Creating process and running python script..."
timeout -s SIGINT $sleep_seconds $PYTHON_PATH $SCRIPT_PATH
echo "Stopped process! Ready for creating backup..."



echo "====== Before start backups ============================================="

connection_check


echo "====== Starting backups ================================================="
# Creating backup on gdrive (logs and db)

gdrive_check

current_timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo "Copying previous terminal logs to gdrive..."
cp -r -u -v $TERMINAL_LOGS_PATH/. $GDRIVE_PATH/backups/terminal_logs/
echo "Copying Discord logs to gdrive..."
cp -r -u -v $DISCORD_LOGS_PATH/. $GDRIVE_PATH/backups/logs/
echo "Copying database.sqlite to gdrive..."
cp -v $WORK_DIR/database.sqlite $GDRIVE_PATH/backups/databases/"$current_timestamp.sqlite"
echo "Copying assets folder to gdrive..."
cp -r -u -v $RANK_CARDS/. $GDRIVE_PATH/backups/assets/images/rank_cards/
echo "Completed!"


echo "====== Script work completed! ==========================================="

# Restarting system for clear memory

echo "Need reboot..."
