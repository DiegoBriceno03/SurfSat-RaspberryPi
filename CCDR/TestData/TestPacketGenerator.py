import sys
import zlib
import bitstring

### EXAMPLE PICOSCOPE DATA PACKET ###
########## 256 BYTE PACKET ##########
#
#  #######  12 BYTE HEADER #######  
#  #  2 bits - System Identifications
#  #  9 bits - Picoscope Status (<0x140)
#  # 60 bits - Data Start Timestamp (integer number of nanoseconds; can store >6.5 years)
#  #  1 bits - Data Timestep Units (us/ns)
#  # 10 bits - Data Timestep (in units above)
#  #  2 bits - Triggering Channel
#  # 12 bits - Unused
#  ###############################
#
#  ## 240 BYTE (60 SAMPLE) BODY ##
#  #  8 bits - Channel A
#  #  8 bits - Channel B
#  #  8 bits - Channel C
#  #  8 bits - Channel D
#  ###############################
#
#  ####### 4 BYTE CHECKSUM #######
#  # 32 bits - Checksum
#  ###############################
#
#####################################

filename = 'testpacket.pkt'

# Create Bits objects with fake data of correct length 
sys_ident   = bitstring.Bits('0b11')
pico_status = bitstring.Bits('0b111110110')
start_time  = bitstring.Bits('0b1110010111010100110000111011001010100010001010110011')
time_units  = bitstring.Bits('0b1')
timestep    = bitstring.Bits('0b1000100110')
trigger     = bitstring.Bits('0b10')
unused      = bitstring.Bits('0b10111100110111101111')

# Generate BitStream for header with this fake data
header = bitstring.BitStream()
header.append(sys_ident)
header.append(pico_status)
header.append(start_time)
header.append(time_units)
header.append(timestep)
header.append(trigger)
header.append(unused)
print("Header (%d bytes):\n%s" % (len(header.bytes), header))

# Generate incrementing bytes to act as fake sample values to fill out the packet
body = bitstring.BitStream()
for i in range(4*60):
	body.append(bitstring.Bits(hex=('0x%02x' % i)))
sys.stdout.write("\nBody (%d bytes):" % len(body.bytes))
for i, v in enumerate(body.bytes):
	if i % 16 == 0: sys.stdout.write("\n")
	sys.stdout.write("%02x" % v)
sys.stdout.write("\n")

# Compute a CRC32 checksum from the concatenated header and body
checksum = bitstring.Bits(hex=('0x%08x' % (zlib.crc32(header.bytes + body.bytes) & 0xFFFFFFFF)))
print("\nCRC32 (%d bytes):\n%s" % (len(checksum.bytes), checksum))

# Combine header, body, and checksum into one full packet
packet = header + body + checksum
sys.stdout.write("\nFull Packet (%d bytes):" % len(packet.bytes))
for i, v in enumerate(packet.bytes):
	if i % 16 == 0: sys.stdout.write("\n")
	sys.stdout.write("%02x" % v)
sys.stdout.write("\n")

# Write packet out to binary file
# NOTE: use `xxd testpacket.pkt` on command line to verify output
with open(filename, 'wb') as fh:
	fh.write(packet.bytes)
