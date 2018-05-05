#define PIN_RESET   2
#define PIN_ENABLE  3
#define PIN_STATUS 13

// Define global boolean to track science vs idle mode
boolean sciencemode = false;
boolean sciencedelay = true;

// Define global long integer to track simulated data
unsigned long data = 0x00000000;

void setup()
{

	// PLP uses 115200 8N1 UART
	Serial.begin(115200);

	// Configure onboard LED to indicate science mode
	pinMode(PIN_STATUS, OUTPUT);
	digitalWrite(PIN_STATUS, LOW);

	// Configure inputs defining RESET and ENABLE signals
	pinMode(PIN_RESET,  INPUT_PULLUP); // active low signal
	pinMode(PIN_ENABLE, INPUT);        // active high signal

}

void loop()
{

	// If RESET is active, clear data, and stop transmit
	if( digitalRead(PIN_RESET) == LOW )
	{
		data = 0x00000000;
		sciencemode = false;
	}
	// If ENABLE is inactive, keep data, but stop transmit
	else if( digitalRead(PIN_ENABLE) == LOW )
	{
		sciencemode = false;
	}

	// PLP sends four bytes for every sample in science mode
	if( sciencemode )
	{

		// Delay for 5 ms once science mode is enabled
		if(sciencedelay)
		{
			sciencedelay = false;
			delay(5);
		}	

		// Define character array to store TX data
		char datastr[4] = {};

		// Update data string with values from integer
		for( char i = 0; i < 4; i++ )
			datastr[3-i] = (data >> i*8) & 0xFF;

		// Transmit data string over serial port
		for( char i = 0; i < 4; i++ )
			Serial.print(datastr[i]);

		// Increment the simulated data variable
		data += 0x00000001;

	}
	else
	{
		// Reset flags if science mode disabled
		sciencedelay = true;
	}

	// Send data at a cadence of 715 Hz (1.4 ms)
	delayMicroseconds(1400);

}

void serialEvent()
{

	// Read in buffered data when serial interrupt is detected
	while(Serial.available())
	{

		char inChar = (char)Serial.read();

		// If command byte has a 1 in the MSB, enter science mode
		// Otherwise, enter idle mode and await new command byte
		sciencemode = (inChar & 0x80);

		// Update LED to indicate science mode status
		digitalWrite(PIN_STATUS, sciencemode ? HIGH : LOW);

	}

}
