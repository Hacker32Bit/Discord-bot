#!/bin/bash

LOG="/home/gektor/Discord-bot/logs/wifi_watchdog.log"
PING_TARGET="8.8.8.8"

if ! ping -c 1 -W 2 $PING_TARGET &>/dev/null; then
  echo "$(date): No internet, restarting Wi-Fi" >> $LOG
  nmcli radio wifi off
  sleep 2
  nmcli radio wifi on
  sleep 10
  nmcli con up id "Ucom8566_2.4G" >> $LOG 2>&1
else
  echo "$(date): Internet OK" >> $LOG
fi