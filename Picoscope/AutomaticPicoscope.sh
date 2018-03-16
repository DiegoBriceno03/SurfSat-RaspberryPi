#!/bin/bash

savedir=data
mkdir -p $savedir

# -A autoname
# -O data output directory
# -G save/show graph
# -T enable trigger
# -C set trigger channel
# -V set vertical trigger level
# -H set horizontal trigger level
# -D set trigger direction
# -W set trigger wait time
# -s set number of samples
# -i set sample interval
python block_capture.py -A -O $savedir -G -T -C0 -V0.2 -H0.2 -D2 -W25000000 -s10000 -i4
