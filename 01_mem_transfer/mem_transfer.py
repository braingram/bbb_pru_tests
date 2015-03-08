''' mem_transfer.py
transfer a 4 byte number to the pru, add 1'''

PRUSS0_PRU0_DATARAM    = 0
PRUSS0_PRU1_DATARAM    = 1
PRUSS0_PRU0_IRAM       = 2
PRUSS0_PRU1_IRAM       = 3
PRUSS0_SHARED_DATARAM  = 4

import pypruss								# The Programmable Realtime Unit Library
import struct
import mmap


PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024

SHAREDRAM_START = 0x00012000

set_value = 0

print("Set value: %s" % set_value)
with open("/dev/mem", "r+b") as f:	       
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
    ddr_mem[SHAREDRAM_START:SHAREDRAM_START+4] = struct.pack('L', set_value)


pypruss.init()								# Init the PRU
pypruss.open(0)								# Open PRU event 0 which is PRU0_ARM_INTERRUPT
pypruss.pruintc_init()						# Init the interrupt controller
pypruss.exec_program(1, "./mem_transfer.bin")			# Load firmware "mem_transfer.bin" on PRU 0
pypruss.wait_for_event(0)					# Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
pypruss.clear_event(0)						# Clear the event
pypruss.exit()								# Exit


read_value = 0
with open("/dev/mem", "r+b") as f:	       
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
    read_value = struct.unpack('L', ddr_mem[SHAREDRAM_START:SHAREDRAM_START+4])
print("Read value: %s" % read_value)
