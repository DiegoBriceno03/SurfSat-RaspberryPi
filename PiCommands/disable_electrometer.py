import pigpio

pi = pigpio.pi()
pi.set_mode(9, pigpio.OUTPUT)
pi.write(9, 0)
pi.stop()
