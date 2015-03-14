#!/usb/bin/env python
# failsafe.py
# turn on a gpio, keep it on as long as the failsafe is reset
# before it reaches 0'''

import struct
import time
import mmap

import pypruss

PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024

SHAREDRAM_START = 0x00012000

failsafe_value = (1000 * 1000 * 200) / 6 # 1 second

def write_failsafe(failsafe_value):
    print("Failsafe: %s" % failsafe_value)
    with open("/dev/mem", "r+b") as f:	       
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
        print("write %s to [%s:%s]" % (failsafe_value, hex(SHAREDRAM_START), hex(SHAREDRAM_START+4)))
        ddr_mem[SHAREDRAM_START:SHAREDRAM_START+4] = struct.pack('L', failsafe_value)


def read_failsafe():
    with open("/dev/mem", "r+b") as f:
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
        value = struct.unpack('L', ddr_mem[SHAREDRAM_START:SHAREDRAM_START+4])
        print("read %s from [%s:%s]" % (value, hex(SHAREDRAM_START), hex(SHAREDRAM_START+4)))
    return value


def read_gpio():
    pass


def start_program():
    pypruss.modprobe() 	       	# This only has to be called once pr boot
    pypruss.init()			# Init the PRU
    pypruss.open(0)			# Open PRU event 0 which is PRU0_ARM_INTERRUPT
    pypruss.pruintc_init()		# Init the interrupt controller
    pypruss.exec_program(0, "./failsafe.bin")  # Load firmware "blinkled.bin" on PRU 0

def wait_for_interrupt():
    pypruss.wait_for_event(0)	# Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
    pypruss.clear_event(0)		# Clear the event
    pypruss.pru_disable(0)		# Disable PRU 0, this is already done by the firmware
    pypruss.exit()			# Exit, don't know what this does. 


if __name__ == '__main__':
    write_failsafe(failsafe_value)
    print("Failsafe: %s" % read_failsafe())
    start_program()
    for i in xrange(10):
        time.sleep(0.8)
        print("Failsafe[%s]: %s" % (i, read_failsafe()))
        write_failsafe(failsafe_value)
        print("Failsafe[%s]: %s" % (i, read_failsafe()))
    for i in xrange(5):
        time.sleep(0.8)
        print("Failsafe[%s]: %s" % (i, read_failsafe()))
    wait_for_interrupt()
