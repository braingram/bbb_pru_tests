#!/bin/bash
echo heartbeat > /sys/class/leds/beaglebone\:green\:usr0/trigger
echo mmc0 > /sys/class/leds/beaglebone\:green\:usr0/trigger
echo cpu0 > /sys/class/leds/beaglebone\:green\:usr0/trigger
echo mmc1 > /sys/class/leds/beaglebone\:green\:usr0/trigger
