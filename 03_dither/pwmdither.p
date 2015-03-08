//
// PWM with dither on the PRU
//
// 1) setup pru
// 2) load parameters from main memory (> 0x00080000 through L3)
// 3) store the parameters locally (for faster access)
// 4) setup pwm counters from local memory
// 5) generate pwm period
// 6) check for cpu->pru interrupt, if: goto 2, else: goto 4
//
// params needed are
// 1) pwm period in loop counts (NOT ticks)
// 2) on count in loop counts
// 3) ddelta in loop counts (modifies oncount)
// 4) dvalue in loop counts (max oncount modification)
//
// registers needed
// dither value delta direction (dvd) [0 or 1] [shared]
// dither value [0 to ?] [shared]
// period count [shared]
// oncount0, onlocal1, ... [local, per channel]
//
// 1st loop: 21 ops [+6] from enable
//      : 105 - 135 ns
// tight loop: 15 ops [+6]
//      : 75 - 105 ns
// period reset: 11 or 13 ops to get to read values, +14 to get to enable [25-27 ops]
//      : 125 - 135 ns

#define PERIOD r0
#define DDELTA r1
#define DVALUE r2
#define ONCOUNT0 r3
#define ONCOUNT1 r4
#define ONCOUNT2 r5
#define ONCOUNT3 r6
#define ONCOUNT4 r7
#define ONCOUNT5 r8
#define FAILSAFE r9
#define ENABLE r10
#define DVD r11
#define DV r12

.origin 0
.entrypoint START

START:  // do some 1 time setup
    // L3 should only be needed for pru -> cpu memory access
    LBCO r0, C4, 4, 4		// load prucfg
    CLR  r0, r0, 4		// clear prucfg bit 4 (enable L3 interconnect)
    SBCO r0, C4, 4, 4		// enable L3 interconnect

    // TODO these will need to be reset when dither settings change
    ZERO DV, 4
    MOV DVD, 1

READVALUES: // 11 ops
    // read parameters
    // r0 : period
    // r1 : ddelta
    // r2 : dvalue
    // r3, 4, 5, 6, 7, 8 : on periods
    // r9 : failsafe
    // r10 : enable (pre-calculated)
    // r11 : dvd
    // r12 : dv

    LBCO r0, C28, 0, 44		// reads in r0-10 from shared ram
    // TODO what to do when dither changes, need to reset DV and DVD

SETOUTPUTS: // 9 ops
    QBEQ ABORT, FAILSAFE, 0         // has failsafe counter elapsed?
    SUB FAILSAFE, FAILSAFE, 1       // decrement failsafe counter
    // set outputs to enable buffer
    MOV r30, ENABLE                 // TODO set only a subset of bytes?
    // set oncounts to oncount + dv
    ADD ONCOUNT0, ONCOUNT0, DV
    ADD ONCOUNT1, ONCOUNT1, DV
    ADD ONCOUNT2, ONCOUNT2, DV
    ADD ONCOUNT3, ONCOUNT3, DV
    ADD ONCOUNT4, ONCOUNT4, DV
    ADD ONCOUNT5, ONCOUNT5, DV

CHECK0:
    QBNE CHECK1, ONCOUNT0, 0
    CLR r30.t0
CHECK1:
    QBNE CHECK2, ONCOUNT1, 0
    CLR r30.t1
CHECK2:
    QBNE CHECK3, ONCOUNT2, 0
    CLR r30.t2
CHECK3:
    QBNE CHECK4, ONCOUNT3, 0
    CLR r30.t3
CHECK4:
    QBNE CHECK5, ONCOUNT4, 0
    CLR r30.t4
CHECK5:
    QBNE CHECKPERIOD, ONCOUNT5, 0
    CLR r30.t5
    // 12 ops

CHECKPERIOD: // 8 ops
    SUB PERIOD, PERIOD, 1
    QBEQ RESETPERIOD, PERIOD, 0
    SUB ONCOUNT0, ONCOUNT0, 1
    SUB ONCOUNT1, ONCOUNT1, 1
    SUB ONCOUNT2, ONCOUNT2, 1
    SUB ONCOUNT3, ONCOUNT3, 1
    SUB ONCOUNT4, ONCOUNT4, 1
    SUB ONCOUNT5, ONCOUNT5, 1
    QBA CHECK0

RESETPERIOD: // 5 ops
    QBEQ INCDITHER, DVD, 1
    SUB DV, DV, DDELTA
    // dv = 0? dvd = 1
    QBNE READVALUES, DV, 0
    MOV DVD, 1
    QBA READVALUES

INCDITHER:  // 4 ops
    ADD DV, DV, DDELTA
    // dv = dvalue? dvd = 0
    QBLT READVALUES, DV, DVALUE
    MOV DVD, 0
    QBA READVALUES

HALT
