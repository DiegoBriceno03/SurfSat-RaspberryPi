import sys
import zlib
import bitstring

#### HEADER ####
#  2 bits - System Identifications
#  9 bits - Picoscope Status (<0x140)
# 52 bits - Data Start Timestamp (integer number of microseconds; can store >48 years)
#  1 bits - Data Timestamp Units (us/ns)
# 10 bits - Data Timestamp (in units above)
#  2 bits - Triggering Channel
# 20 bits - unused

# 12 byte header

#### BODY ####
#  8 bits - Channel A
#  8 bits - Channel B
#  8 bits - Channel C
#  8 bits - Channel D

#  4 byte sample * 28 samples to fill out packet

#### CHECKSUM ####
# 32 bits - Checksum

#  4 byte checksum

##################

# Create Bits objects with fake data of correct length 
sys_ident   = bitstring.Bits('0b00')
pico_status = bitstring.Bits('0b000000000')
start_time  = bitstring.Bits('0b0000000000000000000000000000000000000000000000000000')
time_units  = bitstring.Bits('0b0')
timestamp   = bitstring.Bits('0b0000000000')
trigger     = bitstring.Bits('0b00')
unused      = bitstring.Bits('0b00000000000000000000')

# Generate BitStream for header with this fake data
header = bitstring.BitStream()
header.append(sys_ident)
header.append(pico_status)
header.append(start_time)
header.append(time_units)
header.append(timestamp)
header.append(trigger)
header.append(unused)
print("Header (%d bytes):\n%s" % (len(header.bytes), header))

# Generate incrementing bytes to act as fake sample values to fill out the packet
body = bitstring.BitStream()
for i in range(4*28):
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
