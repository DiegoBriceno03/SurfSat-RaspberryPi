#!/bin/bash

echo "To exit, remember to press ctrl-a K (lowercase a and capital K for kill)."
echo
read -p "Hit enter to continue... "

screen /dev/serial0 115200
