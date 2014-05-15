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

    MOV r30.b0, 0x00


READ_PARAMS:
    // read blink count and duration (in ticks)
    LBCO r0, C28, 0, 8		// reads in r0 (count) and r1 (duration)

BLINK_ON:
    MOV r2, r1
    MOV r30.b0, 0x01

DELAY_ON:
    SUB r2, r2, 1
    QBNE DELAY_ON, r2, 0

BLINK_OFF:
    MOV r2, r1
    MOV r30.b0, 0x02

DELAY_OFF:
    SUB r2, r2, 1
    QBNE DELAY_OFF, r2, 0

COUNT_DOWN:
    SUB r0, r0, 1
    QBNE BLINK_ON, r0, 0
    MOV r30.b0, 0x00
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion

HALT
