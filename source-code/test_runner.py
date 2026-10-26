#!/usr/bin/env python3
"""
ARINC826Forge Pro — Automated Unit & Regression Test Suite
10 Comprehensive Verification Tests for ARINC 826 CAN Loader Engine
"""

import unittest
from arinc826_cli import ARINC826Simulator

class TestARINC826ForgePro(unittest.TestCase):
    def setUp(self):
        self.sim = ARINC826Simulator()

    def test_01_can_29bit_identifier_generation(self):
        """Test 01: ARINC 825 29-Bit Extended CAN Identifier Construction"""
        can_id = self.sim.format_29bit_can_id(2, 0x12, 0x01, 0x1A)
        self.assertTrue(can_id.startswith("0x"))
        can_int = int(can_id, 16)
        self.assertLess(can_int, (1 << 29))

    def test_02_session_initialization(self):
        """Test 02: Loader Session Initialization Lifecycle (IDLE -> HEADER_TRANSFER)"""
        res = self.sim.init_session()
        self.assertEqual(res["status"], "INITIALIZED")
        self.assertEqual(self.sim.session_state, "HEADER_TRANSFER")

    def test_03_flow_control_block_transfer(self):
        """Test 03: Flow Control Segmented Block Transfer Stepping"""
        self.sim.init_session()
        res = self.sim.transfer_block()
        self.assertEqual(res["state"], "BLOCK_TRANSFER")
        self.assertEqual(res["block"], 1)
        self.assertGreater(res["progress_pct"], 0)

    def test_04_full_payload_commit(self):
        """Test 04: Full 64-Block Upload Completion to Verification & Commit"""
        self.sim.init_session()
        for _ in range(self.sim.total_blocks):
            res = self.sim.transfer_block()
        self.assertEqual(self.sim.session_state, "COMMIT")
        self.assertEqual(res["block"], 64)
        self.assertEqual(self.sim.crc32_calculated, self.sim.crc32_expected)

    def test_05_dual_bank_flash_toggle(self):
        """Test 05: Target Dual-Bank Flash Alternation on Commit"""
        initial_bank = self.sim.active_bank
        self.sim.init_session()
        for _ in range(self.sim.total_blocks):
            self.sim.transfer_block()
        self.assertNotEqual(self.sim.active_bank, initial_bank)

    def test_06_gate_safety_interlock_airborne(self):
        """Test 06: Weight-on-Wheels Airborne Inhibit Protection"""
        self.sim.weight_on_wheels = False # Airborne
        res = self.sim.init_session()
        self.assertEqual(res["status"], "ABORTED")
        self.assertEqual(self.sim.session_state, "ABORT")

    def test_07_gate_safety_interlock_engine(self):
        """Test 07: Engine Running Safety Inhibit Protection"""
        self.sim.weight_on_wheels = True
        self.sim.engines_running = True # Engine spooling
        res = self.sim.init_session()
        self.assertEqual(res["status"], "ABORTED")
        self.assertEqual(self.sim.session_state, "ABORT")

    def test_08_arinc429_label279_parity(self):
        """Test 08: ARINC 429 Label 279 Bit 32 Odd Parity Verification"""
        words = self.sim.generate_arinc429_words()
        word279_int = int(words["label279"], 16)
        bit_count = bin(word279_int).count('1')
        self.assertEqual(bit_count % 2, 1, f"Label 279 parity must be odd (bits: {bit_count})")

    def test_09_arinc429_label300_parity(self):
        """Test 09: ARINC 429 Label 300 Bit 32 Odd Parity Verification"""
        words = self.sim.generate_arinc429_words()
        word300_int = int(words["label300"], 16)
        bit_count = bin(word300_int).count('1')
        self.assertEqual(bit_count % 2, 1, f"Label 300 parity must be odd (bits: {bit_count})")

    def test_10_abort_counter_increment(self):
        """Test 10: Session Abort Interception Counter Increment"""
        initial_aborts = self.sim.aborts_triggered
        self.sim.weight_on_wheels = False
        self.sim.init_session()
        self.assertEqual(self.sim.aborts_triggered, initial_aborts + 1)

if __name__ == "__main__":
    unittest.main()
