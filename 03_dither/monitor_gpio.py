#!/usr/bin/env python

import time

import Adafruit_BBIO.GPIO as GPIO


GPIO.setup("P9_26", GPIO.IN)

t0 = time.time()

try:
    while True:
        GPIO.wait_for_edge("P9_26", GPIO.RISING)
        t1 = time.time()
        print (t1 - t0)
        t0 = t1
except ImportError:
    pass
