.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19

// it's probably much faster (and better) to do this through r30
#define GPIO1 			0x4804c000		// The adress of the GPIO1 
#define GPIO_CLEARDATAOUT 	0x190
#define GPIO_SETDATAOUT 	0x194

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


READ_PARAMS:
    // read blink count and duration (in ticks)
    LBCO r0, C28, 0, 8		// reads in r0 (count) and r1 (duration)

BLINK_ON:
    MOV r2, r1			// set r2 to duration for countdown
    MOV r4, 7<<22
    MOV r3, GPIO1 | GPIO_SETDATAOUT
    SBBO r4, r3, 0, 4

DELAY_ON:
    SUB r2, r2, 1
    QBNE DELAY_ON, r2, 0

BLINK_OFF:
    MOV r2, r1			// set r2 to duration for countdown
    MOV r4, 7<<22
    MOV r3, GPIO1 | GPIO_CLEARDATAOUT
    SBBO r4, r3, 0, 4

DELAY_OFF:
    SUB r2, r2, 1
    QBNE DELAY_OFF, r2, 0

COUNT_DOWN:
    SUB r0, r0, 1
    QBNE BLINK_ON, r0, 0
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion

HALT
