.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19

START:
    // L3 should only be needed for pru -> cpu memory access
    LBCO r0, C4, 4, 4		// load prucfg
    CLR  r0, r0, 4		// clear prucfg bit 4 (enable L3 interconnect)
    SBCO r0, C4, 4, 4		// enable L3 interconnect

    MOV  r0, 0x0120		// offset sbbo lbbo to shared memory (0x0100) + other pru (0x20)
    MOV  r1, 0x00022028
    SBBO r0, r1, 0, 4		// writes 0x0120 to 0x00022028, pru0
    MOV  r1, 0x00024028
    SBBO r0, r1, 0, 4		// writes 0x0120 to 0x00024028, pru1

    MOV r30.b0, 0x00		// turn off all pru outputs
    ZERO &r0, 8			// clear r0 (new failsafe) and r1 (failsafe)

LOAD_FAILSAFE:
    LBCO r0, C28, 0, 4		// reads in r0 new failsafe
    QBNE SET_FAILSAFE, r0, 0    // if failsafe is not 0, reset the failsafe counter
    QBA CHECK_FAILSAFE

SET_FAILSAFE:
    MOV r1, r0			// reset failsafe counter
    ZERO &r0, 4
    SBCO r0, C28, 0, 4		// clear the new failsafe

CHECK_FAILSAFE:
    QBEQ OUTPUT_OFF, r1, 0	// if failafe is 0, turn output off
    SUB r1, r1, 1		// subtract 1 from failsafe

OUTPUT_ON:
    MOV r30.b0, 0x01		// turn on gpio
    QBA LOAD_FAILSAFE		// go back to beginning of loop

OUTPUT_OFF:
    MOV r30.b0, 0x00
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion

HALT
