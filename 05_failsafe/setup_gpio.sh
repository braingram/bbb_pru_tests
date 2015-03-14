#!/bin/bash
# connect a wire between p9 pin31 and p9 pin26
# now enable gpio 14, p9 pin26
echo 14 > /sys/class/gpio/export
# set it to input
echo in > /sys/class/gpio/gpio14/direction
