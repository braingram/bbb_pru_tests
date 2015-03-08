''' gpio.py
blink a led for a certain number of times'''

import struct
import mmap

import pypruss

# count, duration

PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024

SHAREDRAM_START = 0x00012000

count_value = 20
duration_value = 1000 * 1000 * 100  # 500 ms

print("Count   : %s" % count_value)
print("Duration: %s" % duration_value)
with open("/dev/mem", "r+b") as f:	       
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
    ddr_mem[SHAREDRAM_START:SHAREDRAM_START+4] = struct.pack('L', count_value)
    ddr_mem[SHAREDRAM_START+4:SHAREDRAM_START+8] = struct.pack('L', duration_value)


pypruss.modprobe() 	       	# This only has to be called once pr boot
pypruss.init()			# Init the PRU
pypruss.open(0)			# Open PRU event 0 which is PRU0_ARM_INTERRUPT
pypruss.pruintc_init()		# Init the interrupt controller
pypruss.exec_program(0, "./gpio.bin")  # Load firmware "blinkled.bin" on PRU 0
pypruss.wait_for_event(0)	# Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
pypruss.clear_event(0)		# Clear the event
pypruss.pru_disable(0)		# Disable PRU 0, this is already done by the firmware
pypruss.exit()			# Exit, don't know what this does. 
