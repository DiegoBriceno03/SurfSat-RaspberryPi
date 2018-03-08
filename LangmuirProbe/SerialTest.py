import serial

port = serial.Serial("/dev/serial0", baudrate=115200, timeout=3.0)

port.write("Hello World")
