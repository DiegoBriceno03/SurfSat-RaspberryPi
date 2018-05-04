import pigpio

# Definitions use BCM pin number, comment indicates actual header pin
# number with potential replacement pin number in parentheses
PI_PIN_SDA          =  2 # Header pin  3( 3) # BIDIR
PI_PIN_SCL          =  3 # Header pin  5( 5) # BIDIR
PI_PIN_RX           = 14 # Header pin  8( 8) # INPUT
PI_PIN_TX           = 15 # Header pin 10(10) # OUTPUT
PI_PIN_PICO_ENABLE  = 17 # Header pin 11(11) # OUTPUT
PI_PIN_HEARTBEAT    = 18 # Header pin 12(12) # OUTPUT
PI_PIN_PLP_STATUS   = 22 # Header pin 15(15) # INPUT
PI_PIN_PLP_RESET    = 23 # Header pin 16(16) # OUTPUT
PI_PIN_PLP_ENABLE   = 27 # Header pin 17(13) # OUTPUT  <-- ALWAYS ON; 17 IS VCC
PI_PIN_EM_ALERT1    = 24 # Header pin 18(18) # INPUT
PI_PIN_EM_ALERT2    = 10 # Header pin 19(19) # INPUT
PI_PIN_EM_ENABLE    =  9 # Header pin 21(21) # OUTPUT
PI_PIN_WTC_COMM_IRQ = 25 # Header pin 22(22) # INPUT
PI_PIN_PLP_COMM_IRQ =  8 # Header pin 24(24) # INPUT

class CCDR:
	def __init__(self, pi):

		# Store pigpio instance
		self.pi = pi

		# Define modes of various GPIO pins
		self.pi.set_mode(PI_PIN_PICO_ENABLE, pigpio.OUTPUT)
		self.pi.set_mode(PI_PIN_HEARTBEAT,   pigpio.OUTPUT)
		self.pi.set_mode(PI_PIN_PLP_STATUS,  pigpio.INPUT)
		self.pi.set_mode(PI_PIN_PLP_RESET,   pigpio.OUTPUT)
		self.pi.set_mode(PI_PIN_PLP_ENABLE,  pigpio.OUTPUT)
		self.pi.set_mode(PI_PIN_EM_ALERT1,   pigpio.INPUT)
		self.pi.set_mode(PI_PIN_EM_ALERT2,   pigpio.INPUT)
		self.pi.set_mode(PI_PIN_EM_ENABLE,   pigpio.OUTPUT)

		# Set default states for outputs
		self.pi.write(PI_PIN_PICO_ENABLE, 0)
		self.pi.write(PI_PIN_HEARTBEAT,   1)
		self.pi.write(PI_PIN_PLP_RESET,   1)
		self.pi.write(PI_PIN_PLP_ENABLE,  0)
		self.pi.write(PI_PIN_EM_ENABLE,   0)

	# Boolean sets enable state of gpio pin
	def generic_enable(self, gpio, enable):
		if enable: value = 1
		else:      value = 0
		self.pi.write(gpio, value)

	# Boolean sets enable state of Picoscope
	def enable_picoscope(self, enable):
		self.generic_enable(PI_PIN_PICO_ENABLE, enable)

	# Boolean sets enable state of PLP
	def enable_plp(self, enable):
		self.generic_enable(PI_PIN_PLP_ENABLE, enable)

	# Boolean sets enable state of electrometer
	def enable_electrometer(self, enable):
		self.generic_enable(PI_PIN_EM_ENABLE, enable)

	# Send pulse to active low reset pin of PLP
	def reset_plp(self):
		self.pi.gpio_trigger(PI_PIN_PLP_RESET, 10, 0)
