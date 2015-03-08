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


.origin 0
.entrypoint START

START:  // setup PRU
    // L3 should only be needed for pru -> cpu memory access
    LBCO r0, C4, 4, 4		// load prucfg
    CLR  r0, r0, 4		// clear prucfg bit 4 (enable L3 interconnect)
    SBCO r0, C4, 4, 4		// enable L3 interconnect

    LBCO r0, C28, 0, 40		// reads in r0-9 from shared ram
    // read parameters
    // r0 : period
    // r1 : ddelta
    // r2 : dvalue
    // r3, 4, 5, 6, 7, 8 : on periods
    // r9 : failsafe
	QBEQ	NO_FAILSAFE, r9, 0				// Check to see if failsafe is enabled
	QBEQ	FAILSAFE, r9, 1					// Check to see if failsafe timeout has occured
	SUB		r9, r9, 1						// If not timed out, decrement timeout counter
	SBCO	r9, CONST_PRUSHAREDRAM, 36, 4	// Write timeout counter back to shared RAM
	QBA		NO_FAILSAFE						// Skip failsafe action

FAILSAFE:
	LBCO	r1, CONST_PRUSHAREDRAM, 40, 32	// Overwrite commanded positions with failsafe positions

NO_FAILSAFE:
	MOV		r30.b0, 0xFF					// Turn on all output channels for start of cycle



SETUP_DITHER:
    //

SETUP_PWM:
    LBCO    r0, CONST_PRUSHAREDRAM, 0, 40  // load registers
