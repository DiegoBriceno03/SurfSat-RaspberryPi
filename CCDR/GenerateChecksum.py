import sys
import zlib

if len(sys.argv) != 2:
	print("Please provide exactly one commandline argument!")
	sys.exit(1)
else:
	print("CRC32: 0x%08X" % (zlib.crc32(bytes(sys.argv[1])) & 0xFFFFFFFF))
