#!/usr/bin/env python3
"""
ARINC826Forge Pro — Standalone Python 3 CLI Runner & CAN Bus Simulator
Avionics Data Loading Over Controller Area Network (CAN) Suite
Standards: ARINC Specification 826-1, ARINC 825, ISO 11898-2, RTCA DO-178C
"""

import sys
import json
import time

class ARINC826Simulator:
    def __init__(self):
        self.bitrate = "CAN_1M"
        self.bitrate_bps = 1000000
        self.target_lru = "EEC-PW1000-GEN2"
        self.node_id = 0x1A
        self.active_bank = "BANK_A"
        self.block_size = 16
        self.st_min_ms = 2.0

        self.session_state = "IDLE"
        self.part_number = "LSAP-826-EEC-PW-V42"
        self.total_blocks = 64
        self.current_block = 0
        self.crc32_expected = "9F86D081"
        self.crc32_calculated = None

        self.weight_on_wheels = True
        self.ground_speed = 0.0
        self.engines_running = False
        self.aborts_triggered = 0

    def format_29bit_can_id(self, priority, service_code, src, dst, is_resp=False):
        can_id = ((priority & 0x07) << 26) | \
                 ((service_code & 0x7F) << 18) | \
                 ((src & 0x7F) << 11) | \
                 ((dst & 0x7F) << 4) | \
                 ((1 if is_resp else 0) << 3)
        return hex(can_id)

    def init_session(self):
        if not self.weight_on_wheels or self.ground_speed > 0 or self.engines_running:
            self.session_state = "ABORT"
            self.aborts_triggered += 1
            return {"status": "ABORTED", "reason": "SAFETY_INTERLOCK_VIOLATION"}
        self.session_state = "HEADER_TRANSFER"
        self.current_block = 0
        return {"status": "INITIALIZED", "can_id": self.format_29bit_can_id(2, 0x12, 0x01, self.node_id)}

    def transfer_block(self):
        if self.session_state in ["HEADER_TRANSFER", "BLOCK_TRANSFER"]:
            self.session_state = "BLOCK_TRANSFER"
            if self.current_block < self.total_blocks:
                self.current_block += 1
                if self.current_block == self.total_blocks:
                    self.session_state = "VERIFICATION"
                    self.crc32_calculated = self.crc32_expected
                    self.session_state = "COMMIT"
                    self.active_bank = "BANK_B" if self.active_bank == "BANK_A" else "BANK_A"
            return {
                "state": self.session_state,
                "block": self.current_block,
                "total": self.total_blocks,
                "progress_pct": round((self.current_block / self.total_blocks) * 100)
            }
        return {"state": self.session_state, "error": "INVALID_STATE"}

    def generate_arinc429_words(self):
        # Label 279 (Octal): Session State & Status
        label279 = 0xAF
        state_map = {"IDLE": 0, "INIT": 1, "HEADER_TRANSFER": 2, "BLOCK_TRANSFER": 3, "VERIFICATION": 4, "COMMIT": 5, "ABORT": 6}
        st_val = state_map.get(self.session_state, 0)
        interlock_ok = 1 if (self.weight_on_wheels and self.ground_speed == 0 and not self.engines_running) else 0
        fc_active = 1 if self.session_state == "BLOCK_TRANSFER" else 0

        data279 = ((st_val & 0x07) << 10) | \
                  (fc_active << 13) | \
                  (interlock_ok << 14) | \
                  ((min(15, self.aborts_triggered) & 0x0F) << 15) | \
                  (0x03 << 28)
        word279 = (data279 & 0x7FFFFF00) | label279
        word279 = self.apply_odd_parity(word279)

        # Label 300 (Octal): Blocks Transferred & CAN Rate
        label300 = 0xC0
        rate_val = 2 # CAN_1M
        data300 = ((min(1023, self.current_block) & 0x3FF) << 10) | \
                  ((rate_val & 0x07) << 20) | \
                  (0x03 << 28)
        word300 = (data300 & 0x7FFFFF00) | label300
        word300 = self.apply_odd_parity(word300)

        return {
            "label279": hex(word279),
            "label300": hex(word300),
            "odd_parity_valid": self.verify_odd_parity(word279) and self.verify_odd_parity(word300)
        }

    def apply_odd_parity(self, word):
        bits = word & 0x7FFFFFFF
        count = bin(bits).count('1')
        if count % 2 == 0:
            bits |= (1 << 31)
        return bits

    def verify_odd_parity(self, word):
        return bin(word).count('1') % 2 == 1

def run_cli():
    sim = ARINC826Simulator()
    print("=" * 70)
    print("ARINC826Forge Pro — CAN Bus Avionics Data Loader CLI")
    print("Standards: ARINC Specification 826-1, ARINC 825, ISO 11898-2")
    print("=" * 70)

    print(f"\n[TARGET AVIONICS LRU: {sim.target_lru}]")
    print(f"  Physical CAN Layer : 1.0 Mbps High-Speed (ISO 11898-2)")
    print(f"  CAN Node ID        : {hex(sim.node_id)}")
    print(f"  Active Flash Bank  : {sim.active_bank}")

    init_res = sim.init_session()
    print(f"\n[SESSION INITIALIZATION: {init_res['status']}]")
    print(f"  29-Bit Header CAN ID: {init_res.get('can_id')}")

    # Transfer 10 blocks
    for _ in range(10):
        step = sim.transfer_block()
    print(f"\n[BLOCK TRANSFER IN PROGRESS]")
    print(f"  Blocks Streamed     : {sim.current_block} / {sim.total_blocks} ({step['progress_pct']}%)")
    print(f"  Flow Control Pacing : BS={sim.block_size} frames, STmin={sim.st_min_ms}ms")

    bus = sim.generate_arinc429_words()
    print("\n" + "-" * 70)
    print("ARINC 429 Glass-Cockpit Discrete Bus Output:")
    print(f"  Label 279 (Session State & Status)   : {bus['label279']}")
    print(f"  Label 300 (Blocks Transferred & Rate): {bus['label300']}")
    print(f"  Bit 32 Odd Parity Status             : {'VALID (PASS)' if bus['odd_parity_valid'] else 'INVALID (FAIL)'}")
    print("=" * 70)

if __name__ == "__main__":
    run_cli()
