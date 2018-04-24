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
	pinMode(13, OUTPUT);
	digitalWrite(13, LOW);

}

void loop()
{

	// PLP sends four bytes for every sample in science mode
	if(sciencemode)
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
		for( char i = 0; i < 32; i+=8)
			datastr[i] = (data & (0xFF << i*3)) >> i*3;

		// Transmit the simulated data string
		Serial.print(data);

		// Increment the simulated data variable
		data += 0x00000001;

	}
	else
	{
		// Reset flags if science mode disabled
		if(!sciencedelay)
		{
			sciencedelay = true;
		}
	}

	// Send data at a cadence of 20 Hz (50 ms)
	delay(50);

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
		digitalWrite(13, sciencemode ? HIGH : LOW);

	}

}
