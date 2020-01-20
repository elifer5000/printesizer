# Prints the first line when connecting to the printer
# Use it to find the printer's prompt (if any)
# If it seems to get stuck, there's probably no prompt,
# in which case just press Ctrl-C to exit.
import sys
import time
import telnetlib

ip = "x.x.x.x"  # Replace with printer's IP address
try:
    tn = telnetlib.Telnet(ip, 23)
    time.sleep(1.0)
    line = tn.read_until("\n") # Read first line
    print(line)
except:
    sys.exit("Telnet failure")