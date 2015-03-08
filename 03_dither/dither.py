#!/usr/bin/env python
"""
So I think I can dither in ~16 instructions per channel
(5 * 16 = 80 ns ->  12.6 MHz)
6 channels per pru would be nice, giving ~3 MHz
giving 2083 kHz / (2 ** 11) -> ~1
So could possibly do 6 channel 2000 kHz 11 bit pwm with 1 pru

A 'reasonable' target would be:

6 channel
10 bit
2000 kHz
200 Hz 10% dither

How am I doing on registers?
dither and period can be shared
"""

import numpy
import pylab

bits = 10
pwmfreq = 5000
ditherfreq = 200
ditheramp = 0.1  # %
# pru freq = 200MHz, timebase = 5 ns
pru_timebase = 5.  # ns


def calculate_pwm(duty, f=2000, df=200, dmax=0.1, bits=10, cycle_time=100):
    """
    cycle_time = cycle time in ns
    """
    period = 1000000000. / f / cycle_time  # pru ticks per period
    oncount = int(period * duty)  # pru ticks for on

    dperiod = period * f / float(df)  # pru ticks per dither period
    dvalue = period * dmax  # dither by percent of period
    ddelta = 2 * dvalue * df / f  # per period oncount change
    return period, oncount, ddelta, dvalue


def build_pwm2(period, oncount, ddelta, dvalue, ncycles=20):
    # on cpu
    enable = oncount != 0

    # setup (done once)
    #period -= 1
    dvd = 1
    dv = 0

    nvalues = int(period * ncycles)  # na
    values = numpy.zeros((nvalues, 2))  # na
    values[:, 0] = numpy.arange(nvalues)  # na

    # start of loop
    vi = 0  # na
    while vi < nvalues:
        v = enable
        oc = oncount + dv
        pc = period
        while pc > 0:
            values[vi, 1] = v
            vi += 1
            if oc == 0:
                v = 0
            pc -= 1
            oc -= 1
        if dvd:
            dv += ddelta
        else:
            dv -= ddelta
        if dv == 0:
            dvd = 1
        if dv >= dvalue:
            dvd = 0
        if dv < 0:
            raise Exception
    return values


def build_pwm(period, oncount, ddelta, dvalue,
              cycle_time=100, ncycles=20):
    print("Period: %s" % period)
    print("Oncount: %s" % oncount)
    print("Ddelta: %s" % ddelta)
    print("Dvalue: %s" % dvalue)
    # setup registers
    dvd = 1
    dv = 0
    pc = period
    if oncount == period:
        oc = oncount + 1
    else:
        oc = oncount
    if oncount != 0:
        v = 1
    else:
        v = 0
    nvalues = int(period * ncycles)
    values = numpy.zeros((nvalues, 2))
    for i in xrange(nvalues):
        values[i, 0] = cycle_time * i
        pc -= 1  # 1
        oc -= 1  # 2
        if oc == 0:  # 3
            v = 0  # 4
        values[i, 1] = v  # 5
        if pc == 0:  # 6
            pc = period  # 7
            if oncount == period:  # 8
                oc = oncount + 1  # 9
            else:
                oc = oncount + dv  # 10
            if dvd:  # 11
                dv += ddelta  # 12
            else:
                dv -= ddelta  # 13
            if dv <= 0:  # 14
                dvd = 1  # 15
            if dv >= dvalue:  # 16
                dvd = 0  # 17
            print(dv, oc, dvd)
            if oncount != 0:  # 18
                v = 1  # 19
    return values


def plot(vs, period=1.):
    ax = pylab.subplot(211)
    pylab.plot(vs[:, 0], vs[:, 1])
    pylab.ylim(-0.1, 1.1)
    pylab.subplot(212, sharex=ax)
    dvs = vs[1:, 1] - vs[:-1, 1]
    rts = vs[dvs == 1, 0]
    fts = vs[dvs == -1, 0]
    while len(fts) and fts[0] < rts[0]:
        fts = fts[1:]  # skip first fall time
    while len(rts) > len(fts):
        rts = rts[:-1]  # skip last rise time
    dcs = fts - rts
    pylab.plot(rts, dcs / period)
    pylab.scatter(rts, dcs / period)
    pylab.xlim(vs[0, 0], vs[-1, 0])


def plot_duty_cycles(dcs=None, ncycles=100):
    if dcs is None:
        dcs = [v / 10. for v in xrange(11)]
    for dc in dcs:
        plot(build_pwm(*calculate_pwm(dc), ncycles=ncycles))


def pwm(duty, f=5000, df=200, bits=10, ticks_per_update=20):
    vrange = 2 ** bits
    # assuming 32 bit control, calculate timebase
    tb = (1. / f) / float(vrange) * 1000000000.
    print "Timbase(ns): ", tb
    if tb < 5:
        raise Exception("timebase is shorter than 1 instruction %s" % tb)
    pcount = int((1000000000. / f) / pru_timebase)  # period in pru ticks
    print "pru ticks per cycle: %s" % pcount
    print "pru ticks per update: %s" % (pcount / vrange)
    #dithermax = int(ditheramp * vrange)
    dithermax = int(ditheramp * pcount)
    print "max dither ticks: %s" % dithermax
    #oncount = int(duty * vrange)
    oncount = int(duty * pcount)
    print "oncount ticks: %s" % oncount
    dc = 0  # register
    dcd = 1  # register bit
    ds = dithermax / 10.  # use this to set the dither frequency
    pc = pcount  # register
    oc = oncount  # register
    v = 1
    values = []
    nvalues = pcount * 10.
    while len(values) < nvalues:
        pc -= 1
        oc -= 1
        if oc == 0:
            v = 0
        values.append(v)
        if pc == 0:
            pc = pcount
            oc = oncount + dc
            print(oc, dcd, dc)
            if dcd:
                dc += ds
            else:
                dc -= ds
            if dc <= 0:
                dcd = 1
            if dc >= dithermax:
                dcd = 0
            v = 1
    return values


