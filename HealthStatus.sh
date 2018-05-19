#!/bin/bash

function i2cpoll {

	devices=$(sudo i2cdetect -y 1)
	echo "Enabled I2C Interfaces:"
	addresses="48 49 4c 4d"
	for i in $addresses
	do 

		if [ ! -z "$(echo $devices | grep $i)" ]
		then

			if   [ "$i" == "48" ]
			then echo "  Electrometer Channel 1"
			elif [ "$i" == "49" ]
			then echo "  Electrometer Channel 2"
			elif [ "$i" == "4c" ]
			then echo "  WTC Communications Chip"
			elif [ "$i" == "4d" ]
			then echo "  PLP Communications Chip"
			else echo "  None"
			fi

		fi

	done

}

echo "** INITIAL STATE **"
i2cpoll

echo
echo "** ELECTROMETER TEST **"
echo "Enabling Electrometer"
python PiCommands/enable_electrometer.py
sleep 1
i2cpoll
echo "Taking Electrometer Data"
rm -rf data
python Electrometer/ADCInterruptTest.py &
adcpid=$!
sleep 2
kill -9 $adcpid
data=$(ls data/*.txt)
if [ $(cat "$data" | wc | awk '{print $1}') -gt 5 ]
then echo "Electrometer Data Succcess"
else echo "ELECTROMETER DATA FAILURE"
fi
rm -rf data
echo "Disabling Electrometer"
python PiCommands/disable_electrometer.py
sleep 1
i2cpoll

echo
echo "** LANGMUIR PROBE TEST **"
echo "Running Langmuir Probe Test"
rm data.txt
python CCDR/CCDRFirmwarePLP.py
if [ $(cat data.txt | wc | awk '{print $1}') -gt 5 ]
then echo "Langmuir Probe Data Success"
else echo "LANGMUIR PROBE DATA FAILURE"
fi
rm data.txt

echo
echo "** PICOSCOPE TEST **"
echo "Enabling Picoscope"
python PiCommands/enable_picoscope.py
sleep 1
if [ ! -z "$(lsusb | grep -v 'Bus 001 Device 001')" ]
then echo "USB device connected"
else echo "NO USB DEVICES FOUND!"
fi
echo "Disabling Picoscope"
python PiCommands/disable_picoscope.py
sleep 1
if [ ! -z "$(lsusb | grep -v 'Bus 001 Device 001')" ]
then echo "USB DEVICE STILL CONNECTED!"
else echo "USB device disconnected"
fi
