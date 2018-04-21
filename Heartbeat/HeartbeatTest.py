# Be sure to have pigpiod running as root to handle requests!

import sys
import time
import pigpio

HEARTBEAT_PIN = 18
HEARTBEAT_FREQ = 20
HEARTBEAT_DUTY = 50

# At microsecond granularity, maximum time that can be stored in X number of bytes:
# 3.0 bytes:                                                  16 secs
# 3.5 bytes:                                         04 mins, 28 secs
# 4.0 bytes:                               01 hours, 11 mins, 34 secs
# 4.5 bytes:                               19 hours, 05 mins, 19 secs
# 5.0 bytes:                      12 days, 17 hours, 25 mins, 11 secs
# 5.5 bytes:            6 months, 22 days, 14 hours, 43 mins, 06 secs
# 6.0 bytes: 08 years, 11 months,  1 days, 19 hours, 29 mins, 36 secs

# At millisecond granularity, maximum time that can be stored in X number of bytes:
# 2.0 bytes:                                         01 mins, 05 secs
# 2.5 bytes:                                         17 mins, 28 secs
# 3.0 bytes:                               04 hours, 39 mins, 37 secs
# 3.5 bytes:                      03 days, 02 hours, 33 mins, 55 secs
# 4.0 bytes:           01 months, 18 days, 17 hours, 02 mins, 47 secs 
# 4.5 bytes: 02 years, 02 months, 05 days, 08 hours, 44 mins, 36 secs
# 5.0 bytes: 34 years, 10 months, 02 days, 19 hours, 53 mins, 47 secs

# At second granularity, maximum time that can be stored in X number of bytes:
# 1.0 bytes:                                         04 mins, 15 secs
# 1.5 bytes:                               01 hours, 08 mins, 15 secs
# 2.0 bytes:                               18 hours, 12 mins, 15 secs
# 2.5 bytes:                      12 days, 03 hours, 16 mins, 15 secs
# 3.0 bytes:           06 months, 13 days, 04 hours, 20 mins, 15 secs
# 3.5 bytes: 08 years, 06 months, 03 days, 21 hours, 24 mins, 15 secs
# 4.0 bytes: 68 years, 01 months, 06 days, 06 hours, 28 mins, 15 secs

# Tick is 4 byte integer indicating microseconds elapsed so resets every 71.5 minutes
def heartbeat(gpio, level, tick):
	#print("0x%08X" % tick)
	pass

pi = pigpio.pi()
pi.set_mode(HEARTBEAT_PIN, pigpio.OUTPUT)
pi.hardware_PWM(HEARTBEAT_PIN, HEARTBEAT_FREQ, HEARTBEAT_DUTY*10000)

overflow = False
ticktime = {
	"overflows": 0,
	"zerotick": pi.get_current_tick(),
	"inittime": int(time.time()*1e6)
}

cb = pi.callback(HEARTBEAT_PIN, pigpio.FALLING_EDGE, heartbeat)

def handle_overflow():
	global ticktime, overflow
	difftick = pigpio.tickDiff(ticktime["zerotick"], pi.get_current_tick()) - 0x80000000
	if difftick > 0 and not overflow:
		overflow = True
	elif difftick < 0 and overflow:
		overflow = False
		ticktime["overflows"] += 1

while True:
	try:
		handle_overflow()

		ticktimetest = pi.get_current_tick()
		timetimetest = int(time.time()*1e6)
		ticktimetest = ticktime["overflows"] * 0xFFFFFFFF + ticktimetest- ticktime["zerotick"] + ticktime["inittime"]

		sys.stdout.write("0x%010X 0x%010X %+08d " % (ticktimetest, timetimetest, ticktimetest-timetimetest))
		sys.stdout.flush()

		for i in range(1,5*6+1):
			time.sleep(10)
			sys.stdout.write(".")
			if i % 6 == 0:
				sys.stdout.write(" ")
			sys.stdout.flush()

		print()

	except KeyboardInterrupt:
		print()
		break

cb.cancel()
pi.stop()
