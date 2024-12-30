#!/bin/bash
# Script: my-pi-temp.sh
# Purpose: Display the ARM CPU and GPU  temperature of Raspberry Pi 2/3
# Author: Vivek Gite <www.cyberciti.biz> under GPL v2.x+
# -------------------------------------------------------
cpu=$(</sys/class/thermal/thermal_zone0/temp)

echo "$(date) @ $(hostname)"
echo "-------------------------------------------"
## ******************************************* ##
## NOTE : ADJUST " /opt/vc/bin/vcgencmd " path ##
## ******************************************* ##
echo "GPU => $(/usr/bin/vcgencmd measure_temp | grep  -o -E '[[:digit:]].*')"
com=$(echo "scale=1; ${cpu}/1000")
echo "CPU => $(bc <<< $com)'C"