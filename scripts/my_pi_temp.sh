#!/usr/bin/bash
# Script: my_pi_temp.sh
# Purpose: Display the ARM CPU, GPU temperature and FAN speed
# -------------------------------------------------------

cpu=$(</sys/class/thermal/thermal_zone0/temp)
fan=$(</sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input)

echo "$(date) @ $(hostname)"
echo "-------------------------------------------"

# GPU temperature
echo "GPU => $(/usr/bin/vcgencmd measure_temp | grep -o -E '[[:digit:]].*')"

# CPU temperature
com=$(echo "scale=1; ${cpu}/1000")
echo "CPU => ${com}°C"

# FAN speed
echo "FAN SPEED => ${fan} RPM"