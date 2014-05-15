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
import time

import struct
import mmap

import numpy
try:
    import pylab
    has_pylab = True
except ImportError:
    has_pylab = False

try:
    import pypruss
    has_pru = True
except ImportError:
    has_pru = False


PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024

SHAREDRAM_START = 0x00012000

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
    # TODO floor or ceiling some of these?
    return int(period), oncount, int(ddelta), int(dvalue)


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
    if not has_pylab:
        return
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


def set_shared_ram(values, offset=0):
    if not has_pru:
        return
    with open("/dev/mem", "r+b") as f:
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
        offset += SHAREDRAM_START
        for v in values:
            print("write %s to [%s:%s]" % (int(v), hex(offset), hex(offset+4)))
            ddr_mem[offset:offset+4] = struct.pack('L', int(v))
            offset += 4


def get_shared_ram(n=1, offset=0):
    if not has_pru:
        return
    if n == 0:
        return []
    with open("/dev/mem", "r+b") as f:
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
        offset += SHAREDRAM_START
        values = []
        while len(values) != n:
            v = struct.unpack('L', ddr_mem[offset:offset+4])[0]
            print("read %s from [%s:%s]" % (int(v), hex(offset), hex(offset+4)))
            values.append(v)
            offset += 4
    return values


def run_pru():
    if not has_pru:
        return
    pypruss.modprobe()
    pypruss.init()
    pypruss.open(0)  # Open PRU event 0 which is PRU0_ARM_INTERRUPT
    pypruss.pruintc_init()  # Init the interrupt controller
    # Load firmware "mem_transfer.bin" on PRU 0
    pypruss.exec_program(0, "./pwmdither.bin")


def wait_for_pru():
    # Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
    pypruss.wait_for_event(0)
    pypruss.clear_event(0)  # Clear the event
    pypruss.exit()  # Exit


def hw_set_pwm(duties=None, f=2000, df=200, dmax=0.1, ticks_per_update=21):
    if duties is None:
        duties = [0., 0.2, 0.4, 0.6, 0.8, 1.0]
    print("=== input values ===")
    print("Frequency: %s" % f)
    print("Dither frequency: %s" % df)
    print("Dither amplitude: %s" % dmax)
    print("Setting duty cycles: %s" % duties)
    cycle_time = ticks_per_update * 5.
    rs = []
    for d in duties:
        rs.append(calculate_pwm(
            d, f, df, dmax, bits=10., cycle_time=cycle_time))
        #period, oncount, ddelta, dvalue = r
    # TODO check calculated values
    periods = set([r[0] for r in rs])
    assert len(periods) == 1
    period = list(periods)[0]
    ddeltas = set([r[2] for r in rs])
    assert len(ddeltas) == 1
    ddelta = list(ddeltas)[0]
    dvalues = set([r[3] for r in rs])
    assert len(dvalues) == 1
    dvalue = list(dvalues)[0]
    oncounts = [r[1] for r in rs]
    # compute enable
    enable = 0
    for (i, o) in enumerate(oncounts):
        if o != 0:
            enable += 1 << i
    failsafe = 25000  # run for n cycles
    # PERIOD DDELTA DVALUE ON0 ON1 ON2 ON3 ON4 ON5 FS EN
    print("=== computed values ===")
    print("Oncounts    : %s" % oncounts)
    print("Cycle period: %s" % period)
    print("Dither delta: %s" % ddelta)
    print("Dither value: %s" % dvalue)
    print("Failsafe    : %s" % failsafe)
    print("Enable      : %s" % bin(enable))
    vs = [period, ddelta, dvalue] + oncounts + [failsafe, enable]

    set_shared_ram(vs)


def hw_test():
    duties = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    print("setting duties to: %s" % duties)
    hw_set_pwm(duties)
    run_pru()
    for _ in xrange(6):
        duties = duties[1:] + [duties[0]]
        time.sleep(2)
        print("setting duties to: %s" % duties)
        hw_set_pwm(duties)
    wait_for_pru()
    vs = get_shared_ram(13)
    for (i, v) in enumerate(vs):
        print("\t%02i: %s[%s]" % (i, v, hex(v)))

if __name__ == '__main__':
    if has_pru:
        hw_test()
