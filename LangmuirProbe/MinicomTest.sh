#!/bin/bash

echo "To exit, remember to press ctrl-a Q (lowercase a and capital Q for quit)."
echo
read -p "Hit enter to continue... "

minicom -D /dev/serial0
