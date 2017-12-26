#!/usr/bin/env python
"""\
Printesizer
Read midi input and stream appropiate g-code to telnet connection, to make music

Streaming to ZMorph printer based on:
https://github.com/Smoothieware/Smoothieware/blob/edge/smoothie-stream.py

Midi input (using rtmidi) based on:
https://github.com/SpotlightKid/python-rtmidi/blob/master/examples/basic/midiin_poll.py

Midi notes to gcode based on:
https://github.com/rickarddahlstrand/MIDI-to-CNC/blob/master/mid2cnc.py

"""

# Pulses per unit
# alpha_steps_per_mm 76.19            # Steps per mm for alpha stepper
# beta_steps_per_mm 76.19            # Steps per mm for beta stepper
# gamma_steps_per_mm 1600             # Steps per mm for gamma stepper

# Dimensions
# X: 235
# Y: 250
# Z: 200

import sys
import math
import time
import random
import telnetlib
import rtmidi


from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF

okcnt = 0
linecnt = 0
x=0.0
y=0.0
z=0.0
x_dir=1.0
y_dir=1.0
z_dir=1.0
# For zmorph machine
safemin = [ 0, 0, 0 ]
safemax = [ 225, 240, 200 ]
ppu    = [ 76.19, 76.19, 1600 ]

def reached_limit(current, distance, direction, min, max):

    if ( ( (current + (distance * direction)) < max ) and 
         ( (current + (distance * direction)) > min ) ):
        # Movement in the current direction is within safe limits,
        return False

    elif ( ( (current + (distance * direction)) >= max ) and 
           ( (current - (distance * direction)) >  min ) ):
        # Movement in the current direction violates maximum safe
        # value, but would be safe if the direction is reversed
        return True

    elif ( ( (current + (distance * direction)) <= min ) and 
           ( (current - (distance * direction)) <  max ) ):
        # Movement in the current direction violates minimum safe
        # value, but would be safe if the direction is reversed
        return True

    else:
        # Movement in *either* direction violates the safe working
        # envelope, so abort.
        # 
        print "\n*** ERROR ***"
        print "The current movement cannot be completed within the safe working envelope of"
        print "your machine. Turn on the --verbose option to see which MIDI data caused the"
        print "problem and adjust the MIDI file (or your safety limits if you are confident"
        print "you can do that safely). Aborting."
        exit(2);

def write_raw_sequence(tn, seq):
    sock = tn.get_socket()
    if sock is not None:
        sock.send(seq)

def sendGCode(tn, nownote):
	print('note: {}'.format(nownote))
	global linecnt
	global okcnt, x, y, z, x_dir, y_dir, z_dir
	distance_xyz = [1, 0, 0] #TODO calculate
	freq = pow(2.0, (nownote-69)/12.0)*440.0
	feed_xyz = [0, 0]
	feed_xyz[0] = ( freq * 60.0 ) / ppu[0]
	# feed_xyz[1] = ( freq * 60.0 ) / ppu[1]
	# Turn around BEFORE crossing the limits of the 
	# safe working envelope
	#
	if reached_limit( x, distance_xyz[0], x_dir, safemin[0], safemax[0] ):
		x_dir = x_dir * -1
	
	x = (x + (distance_xyz[0] * x_dir))
	
	if reached_limit( y, distance_xyz[1], y_dir, safemin[1], safemax[1] ):
		y_dir = y_dir * -1
	
	y = (y + (distance_xyz[1] * y_dir))
	
	combined_feedrate = math.sqrt(feed_xyz[0]**2 + feed_xyz[1]**2)

	line = 'G01 X{} Y{} F{}'.format(x, y, combined_feedrate)
	print(line)
	tn.write(line + '\n')
	linecnt += 1
	rep = tn.read_eager()
	# print(rep)
	okcnt += rep.count("ok")
	if verbose: print("SND " + str(linecnt) + ": " + line.strip() + " - " + str(okcnt))

	print("Waiting for complete...")
		
	while okcnt < linecnt:
	    rep = tn.read_some()
	    okcnt += rep.count("ok")
	    if verbose: print(str(linecnt) + " - " + str(okcnt))

## parameters
ipaddr = '10.0.0.10'
port = 23
verbose = True

# Prompts user for MIDI input port, unless a valid port number or name
# is given as the first argument on the command line.
# API backend defaults to ALSA on Linux.
midiport = sys.argv[1] if len(sys.argv) > 1 else None

try:
    midiin, port_name = open_midiinput(midiport)
except (EOFError, KeyboardInterrupt):
    sys.exit()

tn = telnetlib.Telnet(ipaddr, port)
# turn on prompt
# write_raw_sequence(tn, telnetlib.IAC + telnetlib.DO + "\x55")

# read startup prompt
tn.read_until("Smoothie command shell")

print("Homing with G28")
tn.write("G28\n")
tn.write("G90\n") #Absolute position
tn.write("G92 X0 Y0 Z0 E0\n") #Set origin to current position

print("Entering main loop. Press Control-C to exit.")
try:
	timer = time.time()
	while True:
		msg = midiin.get_message()
		
		if msg:
			message, deltatime = msg
			timer += deltatime
			print("[%s] @%0.6f %r" % (port_name, timer, message))
			
			if message[0] & 0xF0 == NOTE_ON:
				sendGCode(tn, message[1])
		
		time.sleep(0.01)
except KeyboardInterrupt:
	print('')
finally:
	print("Exit.")
	midiin.close_port()
	del midiin
	tn.write("exit\n")
	tn.read_all()
	tn.close()
	
	print("Done")


# while True:
# 	line = raw_input('-->')

# 	if line == 'quit':
# 		break

# 	tn.write(line + '\n')
# 	linecnt += 1
# 	rep = tn.read_eager()
# 	print(rep)
# 	okcnt += rep.count("ok")
# 	if verbose: print("SND " + str(linecnt) + ": " + line.strip() + " - " + str(okcnt))

# 	print("Waiting for complete...")
		
# 	while okcnt < linecnt:
# 	    rep = tn.read_some()
# 	    okcnt += rep.count("ok")
# 	    if verbose: print(str(linecnt) + " - " + str(okcnt))
	

# print('exiting')		    
# tn.write("exit\n")
# tn.read_all()
# tn.close()

print("Done")



