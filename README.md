# SurfSat-RaspberryPi
## Pi code running Picoscope, Langmuir probe, and electrometer ADC
## Updated 2018/05/09

## Primary Hierarchy

* **CCDR**: Main firmware for interfacing with all subsystems
* **Electrometer**: Read from dual ADCs on electrometer board over I2C using interrupts
* **Heartbeat**: Provide a signal to the WTC as proof of life
* **LangmuirProbe**: Send commands to and receive data from PLP board over hardware UART
* **Picoscope**: Use PicoScope API to collect data from 2000A series oscilloscope

### CCDR

* **CCDR.py**: Class for providing primary CCDR functionality
* **CCDRFirmware.py**: Driver that will eventually integrate all functionality of subsystems, but for now only toggles enables and resets of connected subsystems for very simple testing
* **CCDRFirmwarePLP.py**: Driver that handles collects data from PLP through SC16IS750 chip and saves data
* **CCDRParsePLP.py**: Script that parses data saved from an Arduino flashed with LangmuirProbe/Emulator/Emulator.ino and detects the number of anomalies found in the simulated data
* **SC16IS750.py**: Class for handling I2C/UART conversion through SC16IS750 series chip

### Electrometer

* **ADCInterruptTest.py**: Collect data from electrometer board via interrupts
* **ADCPlot.py**: (*Legacy*) Parse saved data and plot it using matplotlib
* **ADCSimpleTest.py**: (*Legacy*) Collect data from electrometer board via polling
* **ADCThreadingTest.py**: (*Legacy*) Collect data from electrometer using a thread that polls

### Heartbeat

* **HeartbeatTest.py**: Combination heartbeat generator and pigpio tick rollover test

### LangmuirProbe

* **LangmuirProbe.py**: Class for providing PLP board interface
* **LangmuirProbeDriver.py**: Driver for collecting data from PLP board and saving it to file
* **LangmuirProbePlot.py**: Script for parsing file saved by LangmuirProbeDriver.py and plotting via matplotlib
* **LangmuirProbeRun.sh**: Bash script for running LangmuirProbeDriver.py and LangmuirProbePlot.py in sequence

* **Emulator**: 
	* **Emulator.ino**: Arduino source code for emulating the PLP board
	* **SConstruct**: Makefile for compiling and programing Arduino with no need for IDE

* **ExampleData**: Data collected from PLP board in various command modes

* **Legacy**: (*LEGACY*) Old scripts that are historically significant, but no longer of much use

* **Utilities**:
	* **MinicomTest.sh**: Bash script for connecting to hardware UART via Minicom
	* **ScreenTest.sh**: Bash script for connecting to hardware UART via screen
	* **SerialTest.py**: Simple pyserial test of byte string RX/TX

### Picoscope

* **AdvancedTriggerTest.py**: Arm all four channels of Picoscope and run callback when trigger detected on any channel
* **BlockCapture.py**: Modified script provided by PicoTech to capture a single block and plot via matplotlib
* **SimplePicoscopePlot.py**: Capture data on demand from connected Picoscope and plot via matplotlib
* **SimpleStreamingTest.py**: Attempts to enumerate Picoscope connected via USB and output status

* **cblock**: (*LEGACY*)
	* **PicoscopeConsoleControl.exe**: Picoscope interface compiled for x86 from C# source code
	* **PicoscopeBlockVisualizer.py**: Script for parsing the data output by PicoscopeConsoleControl.exe and plotting via matplotlib
	* **PicoscopeBlockDataTest.txt**: An example of data collected by PicoscopeConsoleControl.exe

* **picosdk**: Python bindings for the picosdk provided by PicoTech modified to support Python3 and 2408B Picoscope variant
	* **picostatus.py**: Enumerates the PICO\_STATUS and PICO\_INFO values
	* **ps2000a.py**: Inherited class from ps5000base.py handling 2000A series Picoscope variants
	* **ps5000base.py**: Base class for all Picoscope variants
	* **psutils.py**: Provides helper functions for other Picoscope modules

* **utils**: 
	* **OscilloscopeVisualizer.py**: Script for visualizing data saved from Teledyne Lecroy oscilloscope used for comparisons to Picoscope
