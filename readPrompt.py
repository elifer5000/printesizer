# Prints the first line when connecting to the printer
# Use it to find the printer's prompt (if any)
# If it seems to get stuck, there's probably no prompt,
# in which case just press Ctrl-C to exit.
import sys
import time
import telnetlib

# You can pass the IP as an argument, or just write it here
ip = sys.argv[1] if len(sys.argv) > 1 else "x.x.x.x"  # Replace with printer's IP address

try:
    tn = telnetlib.Telnet(ip, 23)
    time.sleep(1.0)
    line = tn.read_until("\n") # Read first line
    print(line)
    tn.close()
except:
    sys.exit("Telnet failure")