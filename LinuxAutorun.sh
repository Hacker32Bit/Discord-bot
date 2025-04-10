#!/bin/bash

CURRENT_PID=$$
TMP_PATH=$HOME/../../tmp
WORK_DIR=$HOME/Discord-bot
TERMINAL_LOGS_PATH=$TMP_PATH/terminal_logs
DISCORD_LOGS_PATH=$TMP_PATH/logs
PYTHON_PATH=$WORK_DIR/.venv/bin/python
PYTHON_PACKAGES_PATH=$WORK_DIR/.venv/lib/python3.*/site-packages
SCRIPT_PATH=$WORK_DIR/main.py
GDRIVE_PATH=$HOME/mnt/gdrive/Discord-bot
RANK_CARDS=$WORK_DIR/assets/images/rank_cards
END_TIME="06:00:00" # Set time when system should be reboot

mkdir "$TMP_PATH/logs"

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

  while true; do
    if ping -c1 1.1.1.1 &> /dev/null; then
        echo "Internet is available"
        break
    fi
    echo "No internet connection. Retrying in 30 seconds..."
    sleep 30
  done
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

echo "Updating g4f library..."
.venv/bin/pip install -U g4f

echo "-------------------------------------------------------------------------"

echo "Updating customized python modules from files_for_copy..."
rsync -rcv $WORK_DIR/files_for_copy/ $PYTHON_PACKAGES_PATH/

echo "-------------------------------------------------------------------------"

echo "Updating from gdrive '.env', 'database.sqlite', and 'assets/' if they are different..."
gdrive_check

echo "Checking and updating database.sqlite from gdrive..."
mv -v $GDRIVE_PATH/database.sqlite $WORK_DIR/database.sqlite
echo "Checking and updating .env from gdrive..."
rsync -cv $GDRIVE_PATH/.env $WORK_DIR/.env
echo "Checking and updating assets directory from gdrive..."
rsync -rcv $GDRIVE_PATH/backups/assets/ $WORK_DIR/assets/
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
echo "Copying Discord log to gdrive..."
rsync -rcv $DISCORD_LOGS_PATH/ $GDRIVE_PATH/backups/logs/
echo "Copying database.sqlite to gdrive..."
rsync -v $WORK_DIR/database.sqlite $GDRIVE_PATH/backups/databases/"$current_timestamp.sqlite"
echo "Copying assets folder to gdrive..."
rsync -rcv $RANK_CARDS/ $GDRIVE_PATH/backups/assets/images/rank_cards/
echo "Copying terminal log to gdrive..."
rsync -rcv $TERMINAL_LOGS_PATH/ $GDRIVE_PATH/backups/terminal_logs/
echo "Completed!"


echo "====== Script work completed! ==========================================="

# Restarting system for clear memory

echo "Need reboot..."
