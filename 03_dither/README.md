There are 2 options for dither
1. generate pwm & dither on pru
2. use hwpwm & use pru to dither by accessing main memory
3. use hwpwm & use cpu to dither

1 has the benefit of not using the main cpu at all, and not requiring lots of L3 communication.
However, 1 might suffer from timing inconsistencies due to complex pru logic (harder to predict execution time).

2 has the benefit of hardware generated pwm (predictable timing) but requires lots of L3 communication (unpredictable).

3 will potentially tax the cpu because it needs to respond to F (2000) interrupts per second.

If 1 can be made more predictable, this seems reasonable. If not, 2 seems like a decent fallback.
