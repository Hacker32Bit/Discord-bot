#!/bin/bash

CURRENT_PID=$$
WORK_DIR=$HOME/Discord-bot
TERMINAL_LOGS_PATH=$WORK_DIR/terminal_logs
DISCORD_LOGS_PATH=$WORK_DIR/logs
PYTHON_PATH=$WORK_DIR/.venv/bin/python
SCRIPT_PATH=$WORK_DIR/main.py
GDRIVE_PATH=$HOME/mnt/gdrive/Discord-bot
END_TIME="06:00:00" # Set time when system should be reboot


echo() {
  command echo $(date '+%Y-%m-%d %H:%M:%S') "$@"
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

echo "Checking internet availability and waiting for access to network..."

while ! ping -c 1 -W 1 google.com; do
    echo "Waiting for google.com - network interface might be down..."
    sleep 30
done
echo "Connected!"



echo "====== Starting discord.py script ======================================="

# Run python script using python venv
echo "Creating process and running python script..."
cd $WORK_DIR
timeout -s SIGINT $sleep_seconds $PYTHON_PATH $SCRIPT_PATH
echo "Stopped process! Ready for creating backup..."



echo "====== Before start backups ============================================="

echo "Checking internet availability and waiting for access to network..."

while ! ping -c 1 -W 1 google.com; do
    echo "Waiting for google.com - network interface might be down..."
    sleep 30
done
echo "Connected!"



echo "====== Starting backups ================================================="
# Creating backup on gdrive (logs and db)

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


current_timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo "Copying previous terminal logs to gdrive..."
cp -r -u -v $TERMINAL_LOGS_PATH/. $GDRIVE_PATH/backups/terminal_logs/
echo "Copying Discord logs to gdrive..."
cp -r -u -v $DISCORD_LOGS_PATH/. $GDRIVE_PATH/backups/logs/
echo "Copying database.sqlite to gdrive..."
cp -v $WORK_DIR/database.sqlite $GDRIVE_PATH/backups/databases/"$current_timestamp.sqlite"
echo "Completed!"


echo "====== Script work completed! ==========================================="

# Restarting system for clear memory

echo "Need reboot..."
