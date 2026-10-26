/**
 * ARINC826Forge Pro — Core Engine
 * Avionics Data Loading Over Controller Area Network (CAN)
 * Standard References: ARINC Specification 826-1, ARINC 825, ISO 11898-2, RTCA DO-178C, FAA AC 20-115D
 */

class ARINC826Engine {
  constructor() {
    this.canBitrates = {
      'CAN_1M': { name: '1.0 Mbps High-Speed CAN', bitrateBps: 1000000, maxPayloadBytes: 8 },
      'CAN_500K': { name: '500 kbps High-Speed CAN', bitrateBps: 500000, maxPayloadBytes: 8 },
      'CAN_FD_2M': { name: 'CAN FD (2.0 Mbps Data Phase)', bitrateBps: 2000000, maxPayloadBytes: 64 }
    };
    this.activeBitrate = 'CAN_1M';

    // Target LRU Definition
    this.targetLRU = {
      name: 'FADEC EEC Engine Controller (Pratt & Whitney PW1000G)',
      partNumber: 'EEC-PW1000-GEN2',
      nodeID: 0x1A,
      flashBankSizeKB: 2048,
      activeBank: 'BANK_A',
      maxBlockSizeFrames: 16, // Flow Control: 16 frames per block
      separationTimeMs: 2.0   // STmin: 2ms pacing
    };

    // Loader Session State Machine (ARINC 826 §3.2)
    // States: IDLE, INIT, HEADER_TRANSFER, BLOCK_TRANSFER, VERIFICATION, COMMIT, ABORT
    this.sessionState = 'IDLE';

    // Active LSAP Package to Load
    this.activeLSAP = {
      partNumber: 'LSAP-826-EEC-PW-V42',
      totalBytes: 524288, // 512 kB
      totalBlocks: 64,    // 512 kB / (16 frames * 512 bytes)
      currentBlock: 0,
      crc32Expected: '9F86D081',
      crc32Calculated: null
    };

    // Gate Safety Interlocks (FAR 25.1309 / FAA AC 20-115D)
    this.interlocks = {
      weightOnWheels: true,
      groundSpeedKt: 0.0,
      enginesRunning: false,
      maintenanceSwitchLocked: true
    };

    // Frame Telemetry & Counters
    this.stats = {
      framesTransmitted: 0,
      flowControlPauses: 0,
      blocksAcked: 0,
      abortsTriggered: 0,
      crcErrors: 0
    };
  }

  setBitrate(bitrateKey) {
    if (!this.canBitrates[bitrateKey]) throw new Error(`Invalid bitrate: ${bitrateKey}`);
    this.activeBitrate = bitrateKey;
  }

  format29BitCANID(priority, serviceCode, srcNode, dstNode, isResponse = false) {
    // 29-bit ARINC 825 / 826 Identifier Format
    // Bits 28-26: Priority (0-7, 0 highest)
    // Bit 25: Reserved / Doc Type (0)
    // Bits 24-18: Service / Function Code (7 bits)
    // Bits 17-11: Source Node ID (7 bits)
    // Bits 10-4: Destination Node ID (7 bits)
    // Bit 3: Request (0) / Response (1)
    // Bits 2-0: Sub-channel / Reserved (0)
    let canId = 0;
    canId |= (priority & 0x07) << 26;
    canId |= (serviceCode & 0x7F) << 18;
    canId |= (srcNode & 0x7F) << 11;
    canId |= (dstNode & 0x7F) << 4;
    canId |= (isResponse ? 1 : 0) << 3;
    return '0x' + (canId >>> 0).toString(16).toUpperCase().padStart(8, '0');
  }

  initiateSession() {
    // 1. Verify Interlocks
    if (!this.interlocks.weightOnWheels || this.interlocks.groundSpeedKt > 0.0 || this.interlocks.enginesRunning) {
      this.sessionState = 'ABORT';
      this.stats.abortsTriggered++;
      throw new Error('GATE_SAFETY_INTERLOCK_VIOLATION: Data loading over CAN prohibited in-flight or with engines running (FAR 25.1309).');
    }

    this.sessionState = 'INIT';
    this.activeLSAP.currentBlock = 0;
    this.stats.framesTransmitted += 2;
    this.sessionState = 'HEADER_TRANSFER';
    return {
      status: 'INITIALIZED',
      canID: this.format29BitCANID(2, 0x12, 0x01, this.targetLRU.nodeID),
      target: this.targetLRU.name,
      lsapPart: this.activeLSAP.partNumber
    };
  }

  stepBlockTransfer() {
    if (this.sessionState !== 'HEADER_TRANSFER' && this.sessionState !== 'BLOCK_TRANSFER') {
      throw new Error(`Cannot transfer block in state: ${this.sessionState}`);
    }

    this.sessionState = 'BLOCK_TRANSFER';
    if (this.activeLSAP.currentBlock < this.activeLSAP.totalBlocks) {
      this.activeLSAP.currentBlock++;
      this.stats.framesTransmitted += this.targetLRU.maxBlockSizeFrames;
      this.stats.blocksAcked++;
      this.stats.flowControlPauses++;

      if (this.activeLSAP.currentBlock === this.activeLSAP.totalBlocks) {
        this.sessionState = 'VERIFICATION';
        this.verifyAndCommit();
      }
    }

    return {
      sessionState: this.sessionState,
      currentBlock: this.activeLSAP.currentBlock,
      totalBlocks: this.activeLSAP.totalBlocks,
      progressPercent: Math.round((this.activeLSAP.currentBlock / this.activeLSAP.totalBlocks) * 100)
    };
  }

  verifyAndCommit() {
    this.sessionState = 'VERIFICATION';
    // Simulate CRC-32 Verification
    this.activeLSAP.crc32Calculated = this.activeLSAP.crc32Expected;
    this.sessionState = 'COMMIT';
    this.targetLRU.activeBank = this.targetLRU.activeBank === 'BANK_A' ? 'BANK_B' : 'BANK_A';
    return {
      status: 'COMMITTED',
      crc32: this.activeLSAP.crc32Calculated,
      newActiveBank: this.targetLRU.activeBank
    };
  }

  abortSession(reason = 'MANUAL_ABORT') {
    this.sessionState = 'ABORT';
    this.stats.abortsTriggered++;
    return { status: 'ABORTED', reason: reason };
  }

  generateARINC429BusWords() {
    // ARINC 429 Label 279 (Octal): ARINC 826 Session State & Status
    const label279 = 0xAF; // Label 279 representation
    let data279 = 0;

    const stateMap = { IDLE: 0, INIT: 1, HEADER_TRANSFER: 2, BLOCK_TRANSFER: 3, VERIFICATION: 4, COMMIT: 5, ABORT: 6 };
    const stateVal = stateMap[this.sessionState] || 0;
    const interlockBit = (this.interlocks.weightOnWheels && this.interlocks.groundSpeedKt === 0.0 && !this.interlocks.enginesRunning) ? 1 : 0;
    const flowControlBit = this.sessionState === 'BLOCK_TRANSFER' ? 1 : 0;

    data279 |= (stateVal & 0x07) << 10; // Bits 11-13 Session State
    data279 |= (flowControlBit & 0x01) << 13; // Bit 14 Flow Control Pacing Active
    data279 |= (interlockBit & 0x01) << 14; // Bit 15 Safety Interlocks Satisfied
    data279 |= (Math.min(15, this.stats.abortsTriggered) & 0x0F) << 15; // Bits 16-19 Abort Counter
    data279 |= 0x03 << 28; // Bits 29-30 SSM (Normal Operation)

    let word279 = (data279 & 0x7FFFFF00) | (label279 & 0xFF);
    word279 = this.applyOddParity(word279);

    // Label 300 (Octal): Total Blocks Transferred & Active CAN Bitrate
    const label300 = 0xC0;
    let data300 = 0;
    const blocksVal = Math.min(1023, this.activeLSAP.currentBlock);
    const bitrateMap = { CAN_500K: 1, CAN_1M: 2, CAN_FD_2M: 3 };
    const rateVal = bitrateMap[this.activeBitrate] || 2;

    data300 |= (blocksVal & 0x3FF) << 10; // Bits 11-20 Transferred Blocks
    data300 |= (rateVal & 0x07) << 20; // Bits 21-23 CAN Bitrate Key
    data300 |= 0x03 << 28; // Bits 29-30 SSM

    let word300 = (data300 & 0x7FFFFF00) | (label300 & 0xFF);
    word300 = this.applyOddParity(word300);

    return {
      label279: { hex: '0x' + (word279 >>> 0).toString(16).toUpperCase().padStart(8, '0'), parityValid: this.verifyOddParity(word279) },
      label300: { hex: '0x' + (word300 >>> 0).toString(16).toUpperCase().padStart(8, '0'), parityValid: this.verifyOddParity(word300) }
    };
  }

  applyOddParity(word32) {
    let bits = word32 & 0x7FFFFFFF;
    let count = 0;
    for (let i = 0; i < 31; i++) {
      if ((bits >> i) & 1) count++;
    }
    if (count % 2 === 0) {
      bits |= (1 << 31);
    }
    return bits >>> 0;
  }

  verifyOddParity(word32) {
    let count = 0;
    for (let i = 0; i < 32; i++) {
      if ((word32 >>> i) & 1) count++;
    }
    return count % 2 === 1;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ARINC826Engine };
}
