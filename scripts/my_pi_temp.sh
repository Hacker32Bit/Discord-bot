#!/usr/bin/bash
# Script: my_pi_temp.sh
# Purpose: Display the ARM CPU, GPU temperature and FAN speed
# -------------------------------------------------------
cpu=$(</sys/class/thermal/thermal_zone0/temp)
fan=$(</sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input)

echo "$(date) @ $(hostname)"
echo "-------------------------------------------"

# GPU temperature
echo "GPU temp: $(/usr/bin/vcgencmd measure_temp | sed -E "s/.*=([0-9.]+)'C/\1°C/")"

# CPU temperature
com=$(echo "scale=1; ${cpu}/1000")
echo "CPU temp: $(bc <<< $com)°C"

# FAN speed
echo "Fan RPM: ${fan}"