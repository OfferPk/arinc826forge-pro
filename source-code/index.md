## 

ARINC826Forge Pro

v1.0.0 \| Avionics Data Loading Over CAN (ARINC 826 & ARINC 825\) Studio

CAN FLOW CONTROL ACTIVE

### 

CAN Physical & Target Setup

CAN Bus Standard & Bitrate 1.0 Mbps High-Speed CAN (ISO 11898-2) 500 kbps High-Speed CAN CAN FD (2.0 Mbps Data Phase / 64B)

Target Line Replaceable Unit (LRU) PW1000G FADEC Engine Controller (Node 0x1A) LEAP-1B EEC Dual-Channel Controller (Node 0x1B) Aileron Smart Servo Actuator (Node 0x22)

Active Flash Bank: **BANK\_A (EXEC)**

Flow Control Throttling: **BS=16, STmin=2.0ms**

### 

Ground Gate Interlocks (FAR 25.1309)

Weight-on-Wheels (Squat Switch)

---

Ground Speed \< 0.1 kt

---

FADEC Engines Inactive

---

Interlock Status: **SATISFIED (CLEAR)**

### 

CAN Bus Traffic Streamer (29-Bit ARINC 825 Frames)

\[00.000\] CAN BUS INITIALIZED @ 1.0 Mbps (ISO 11898-2 Standard)  
\[00.012\] TARGET EEC PING: Node 0x1A responding on Channel 0

\[00.015\] STANDBY: Awaiting session initialization command...

**LSAP Payload Transfer Progress** (512 kB / 64 Blocks) **0%**

### 

Session Execution Controls

Init Session Stream Block Abort & Rollback

### 

ARINC 429 Cockpit Bus Output

Label 279 (Session State & Interlocks):

0x83AF08AF \[ODD PARITY VALID\]

Label 300 (Blocks Transferred & CAN Rate):

0x812000C0 \[ODD PARITY VALID\]

Bit 32 Parity: **ODD PARITY VERIFIED (PASS)**

### 

10-Point Normative Auditor

✓ ARINC 825 29-Bit Identifier Formats Validated

✓ 7-Phase Session State Machine Conformance

✓ Flow Control (BS=16, STmin=2ms) Throttled

✓ End-to-End CRC-32 Payload Verification Active

✓ Dual-Bank Flash Rollback Preserved

Run Full 10-Point Audit