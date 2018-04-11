#!/bin/bash

python3 LangmuirProbeDriver.py
python3 LangmuirProbePlot.py
echo "Displaying plot..."
gpicview CVvT.png
