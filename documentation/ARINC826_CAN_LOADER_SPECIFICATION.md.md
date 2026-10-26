# ARINC Specification 826-1 Avionics Data Loading Over Controller Area Network Specification

**Document ID**: ARINC826-SPEC-2026-v1.0  
**Normative Standards**: ARINC Specification 826-1, ARINC 825, ISO 11898-2, RTCA DO-178C, FAA AC 20-115D  
**Classification**: Commercial Avionics CAN Bus Data Loading & Microcontroller Flash Update Standard

---

## 1\. Executive Summary & Operational Scope

The **ARINC Specification 826-1 (Avionics Data Loading Over Controller Area Network)** standardizes protocols, frame formats, flow control, and airworthiness safety mechanisms for uploading software parts (ARINC 665 / ARINC 838\) across Controller Area Network (CAN / CAN FD / ARINC 825\) buses.

While Ethernet / AFDX (ARINC 664\) serves high-bandwidth cabin and display avionics, CAN bus dominates weight-sensitive, distributed aircraft subsystems including FADEC Electronic Engine Controllers (EEC), smart flight control actuators, fuel quantity computers, and regional airframe systems. ARINC 826 eliminates proprietary bootloaders by standardizing CAN data loading across commercial airliners and business jets.

---

## 2\. ARINC 825 29-Bit Extended Identifier Addressing

ARINC 826 messages conform to ARINC 825 CAN 2.0B extended 29-bit identifiers:

- **Bits 28-26**: Priority (0-7, with Priority 2 reserved for data loading).  
- **Bit 25**: Document Type / Format indicator.  
- **Bits 24-18**: Service / Function Code (`0x12` Load Request, `0x13` Load Accept, `0x14` Block Transfer).  
- **Bits 17-11**: Source Node Identifier (e.g., `0x01` Loader).  
- **Bits 10-4**: Destination Node Identifier (e.g., `0x1A` Target EEC).  
- **Bit 3**: Request (0) / Response (1) Indicator.  
- **Bits 2-0**: Sub-channel and service variant bits.

---

## 3\. Protocol State Machine & Flow Control (ISO 15765-2)

The loader and target LRU transition through a strict seven-phase deterministic state machine:

1. **IDLE**: Target in standard operational flight mode.  
2. **INIT**: Loader transmits `LOAD_REQUEST`. Target verifies interlocks and transitions to bootloader mode.  
3. **HEADER\_TRANSFER**: Transfers metadata, target memory partition maps, and total payload length.  
4. **BLOCK\_TRANSFER**: Transfers consecutive 8-byte (CAN) or 64-byte (CAN FD) frames segmented into blocks.  
   - **Block Size (BS)**: Configured to 16 frames per block.  
   - **Separation Time (STmin)**: Paced with 2.0 ms inter-frame spacing to avoid microcontroller buffer overruns.  
   - **Block Acknowledgment**: Target verifies block CRC-16 before issuing next flow control grant.  
5. **VERIFICATION**: End-to-end CRC-32 and SHA-256 integrity validation over the entire staged flash image.  
6. **COMMIT**: Target executes atomic flash bank toggle (`BANK_A` \<-\> `BANK_B`) and boots into new software.  
7. **ABORT**: Clean bus release and immediate fallback to the golden execution bank.

---

## 4\. Ground Gate Safety Interlocks (FAR 25.1309)

To guarantee airworthiness and prevent catastrophic inflight flash erasure:

- **Weight-on-Wheels (WOW)**: Mechanically and logically enforced.  
- **Ground Speed Interlock**: Ground speed must strictly equal 0.0 knots.  
- **Engine Shutdown Interlock**: All engines must be completely inactive before FADEC reprogramming.

---

## 5\. ARINC 429 Glass-Cockpit Discrete Bus Output

The CAN Data Loader LRU broadcasts status onto the low-speed aircraft ARINC 429 bus:

- **Label 279 (Octal)**: ARINC 826 Session State & Status  
  - Bits 11-13: Session State (0: IDLE, 1: INIT, 2: HEADER, 3: TRANSFER, 4: VERIFY, 5: COMMIT, 6: ABORT)  
  - Bit 14: Flow Control Pacing Active (1: Pacing)  
  - Bit 15: Safety Interlocks Satisfied (1: Clear)  
  - Bits 16-19: Abort Event Counter  
  - Bits 29-30: SSM (Normal Operation: 11b)  
  - Bit 32: Odd Parity  
- **Label 300 (Octal)**: Blocks Transferred & Active CAN Bitrate  
  - Bits 11-20: Transferred Blocks Counter (0 \- 1023\)  
  - Bits 21-23: Active Bitrate Key (1: 250k, 2: 500k, 3: 1M)  
  - Bits 29-30: SSM  
  - Bit 32: Odd Parity