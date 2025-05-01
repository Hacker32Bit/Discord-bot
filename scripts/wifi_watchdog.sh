#!/bin/bash

PING_TARGET="8.8.8.8"
LOGFILE="/tmp/wifi_watchdog.log"

# Find all active Wi-Fi devices
IFACES=$(nmcli -t -f DEVICE,TYPE,STATE device | grep -E 'wifi:connected' | cut -d: -f1)

if [ -z "$IFACES" ]; then
    # No active Wi-Fi connections
    echo "$(date): No active Wi-Fi interfaces found." >> "$LOGFILE"
else
    if ! ping -c 1 -W 2 "$PING_TARGET" > /dev/null; then
        echo "$(date): Internet down, restarting Wi-Fi..." >> "$LOGFILE"
        for iface in $IFACES; do
            nmcli device disconnect "$iface"
            sleep 5
            nmcli device connect "$iface"
        done
    else
        # No log spam if Internet is fine
        :
    fi
fi
