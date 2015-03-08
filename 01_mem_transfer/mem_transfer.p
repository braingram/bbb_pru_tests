.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19

START:	
    // L3 should only be needed for pru -> cpu memory access
    LBCO r0, C4, 4, 4		// load prucfg
    CLR  r0, r0, 4		// clear prucfg bit 4 (enable L3 interconnect)
    SBCO r0, C4, 4, 4		// enable L3 interconnect

    // this doesn't seem to be necessary
    //MOV  r0, 0x0120		// offset sbbo lbbo to shared memory (0x0100) + other pru (0x20)
    //MOV  r1, 0x00022028
    //SBBO r0, r1, 0, 4		// writes 0x0120 to 0x00022028, pru0
    //MOV  r1, 0x00024028
    //SBBO r0, r1, 0, 4		// writes 0x0120 to 0x00024028, pru1

    // read in value from shared ram
    LBCO r0, C28, 0, 4
    // increment it by 1
    ADD r0, r0, 1
    // write it back to the same place
    SBCO r0, C28, 0, 4

    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
