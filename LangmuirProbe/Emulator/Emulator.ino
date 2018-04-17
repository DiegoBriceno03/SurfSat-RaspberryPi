boolean sciencemode = false;

void setup() {
  // PLP uses 115200 8N1 UART
  Serial.begin(115200);
  pinMode(13, OUTPUT);
}

void loop() {
  // PLP sends four bytes every 1 ms in science mode
  if(sciencemode) Serial.print("abcd");
  delay(1);
}

void serialEvent() {
  char inChar = (char)Serial.read();
  // If command byte has a 1 in the MSB, enter science mode
  // Otherwise, enter idle mode and await new command byte
  sciencemode = (inChar & 0x80);
  digitalWrite(13, sciencemode ? HIGH : LOW);
}
