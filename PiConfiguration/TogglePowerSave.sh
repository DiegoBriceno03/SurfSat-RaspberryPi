#!/bin/bash

path=/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
state=$(cat $path)

if [ "$state" = "ondemand" ]
	then echo "powersave" | sudo tee $path
	else echo "ondemand"  | sudo tee $path
fi
