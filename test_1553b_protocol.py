#!/usr/bin/env python3
"""
Test Suite for MIL-STD-1553B Protocol Implementation
===================================================

This file contains comprehensive tests for the 1553B protocol implementation,
demonstrating various scenarios and edge cases.
"""

import unittest
import struct
from mil_std_1553b import (
    PositionData, AttitudeData, CommandWord, StatusWord, DataWord,
    BusController, RemoteTerminal, Message1553B, SyncPattern
)


class TestPositionData(unittest.TestCase):
    """Test position data encoding/decoding"""
    
    def test_positive_coordinates(self):
        """Test positive X,Y coordinates"""
        pos = PositionData(x=123.45, y=267.89)
        data_bytes = pos.to_bytes()
        decoded = PositionData.from_bytes(data_bytes)
        
        self.assertAlmostEqual(decoded.x, 123.45, places=2)
        self.assertAlmostEqual(decoded.y, 267.89, places=2)
    
    def test_negative_coordinates(self):
        """Test negative X,Y coordinates"""
        pos = PositionData(x=-123.45, y=-267.89)
        data_bytes = pos.to_bytes()
        decoded = PositionData.from_bytes(data_bytes)
        
        self.assertAlmostEqual(decoded.x, -123.45, places=2)
        self.assertAlmostEqual(decoded.y, -267.89, places=2)
    
    def test_zero_coordinates(self):
        """Test zero coordinates"""
        pos = PositionData(x=0.0, y=0.0)
        data_bytes = pos.to_bytes()
        decoded = PositionData.from_bytes(data_bytes)
        
        self.assertEqual(decoded.x, 0.0)
        self.assertEqual(decoded.y, 0.0)
    
    def test_range_limits(self):
        """Test values at the edge of int16 range"""
        # Maximum values that fit in int16 when scaled by 100
        pos = PositionData(x=327.67, y=-327.68)
        data_bytes = pos.to_bytes()
        decoded = PositionData.from_bytes(data_bytes)
        
        self.assertAlmostEqual(decoded.x, 327.67, places=2)
        self.assertAlmostEqual(decoded.y, -327.68, places=2)


class TestAttitudeData(unittest.TestCase):
    """Test attitude data encoding/decoding"""
    
    def test_positive_angles(self):
        """Test positive roll and pitch angles"""
        att = AttitudeData(roll=45.5, pitch=30.25)
        data_bytes = att.to_bytes()
        decoded = AttitudeData.from_bytes(data_bytes)
        
        self.assertAlmostEqual(decoded.roll, 45.5, places=2)
        self.assertAlmostEqual(decoded.pitch, 30.25, places=2)
    
    def test_negative_angles(self):
        """Test negative roll and pitch angles"""
        att = AttitudeData(roll=-45.5, pitch=-30.25)
        data_bytes = att.to_bytes()
        decoded = AttitudeData.from_bytes(data_bytes)
        
        self.assertAlmostEqual(decoded.roll, -45.5, places=2)
        self.assertAlmostEqual(decoded.pitch, -30.25, places=2)
    
    def test_zero_angles(self):
        """Test zero angles"""
        att = AttitudeData(roll=0.0, pitch=0.0)
        data_bytes = att.to_bytes()
        decoded = AttitudeData.from_bytes(data_bytes)
        
        self.assertEqual(decoded.roll, 0.0)
        self.assertEqual(decoded.pitch, 0.0)


class TestCommandWord(unittest.TestCase):
    """Test command word structure"""
    
    def test_receive_command(self):
        """Test BC->RT receive command"""
        cmd = CommandWord(rt_address=5, tr_bit=0, subaddress=1, word_count=2)
        
        self.assertEqual(cmd.rt_address, 5)
        self.assertEqual(cmd.tr_bit, 0)
        self.assertEqual(cmd.subaddress, 1)
        self.assertEqual(cmd.word_count, 2)
        self.assertEqual(cmd.sync, SyncPattern.COMMAND_SYNC.value)
    
    def test_transmit_command(self):
        """Test RT->BC transmit command"""
        cmd = CommandWord(rt_address=10, tr_bit=1, subaddress=2, word_count=4)
        
        self.assertEqual(cmd.rt_address, 10)
        self.assertEqual(cmd.tr_bit, 1)
        self.assertEqual(cmd.subaddress, 2)
        self.assertEqual(cmd.word_count, 4)
    
    def test_command_word_encoding(self):
        """Test command word bit encoding"""
        cmd = CommandWord(rt_address=3, tr_bit=0, subaddress=1, word_count=2)
        
        # Expected bit pattern: RT(3)=00011, T/R(0)=0, SA(1)=00001, WC(2)=00010
        # Binary: 0001100001 00010 = 0x1822
        expected_data = (3 << 11) | (0 << 10) | (1 << 5) | 2
        self.assertEqual(cmd.data, expected_data)


class TestStatusWord(unittest.TestCase):
    """Test status word structure"""
    
    def test_normal_status(self):
        """Test normal status with no errors"""
        status = StatusWord(rt_address=5)
        
        self.assertEqual(status.rt_address, 5)
        self.assertFalse(status.message_error)
        self.assertFalse(status.busy)
    
    def test_error_status(self):
        """Test status with message error"""
        status = StatusWord(rt_address=7, message_error=True, busy=True)
        
        self.assertEqual(status.rt_address, 7)
        self.assertTrue(status.message_error)
        self.assertTrue(status.busy)


class TestDataWord(unittest.TestCase):
    """Test data word structure"""
    
    def test_data_word_creation(self):
        """Test data word creation and parity calculation"""
        data_word = DataWord(0x1234)
        
        self.assertEqual(data_word.data, 0x1234)
        self.assertEqual(data_word.sync, SyncPattern.DATA_SYNC.value)
        
        # Check parity calculation (odd parity)
        ones_count = bin(0x1234).count('1')  # Count of 1s in 0x1234
        expected_parity = 1 if ones_count % 2 == 0 else 0
        self.assertEqual(data_word.parity, expected_parity)


class TestBusController(unittest.TestCase):
    """Test Bus Controller functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.bc = BusController()
        self.rt = RemoteTerminal(address=5)
        self.bc.add_remote_terminal(self.rt)
    
    def test_send_position_data(self):
        """Test sending position data"""
        position = PositionData(x=100.0, y=200.0)
        success = self.bc.send_position_data(5, position)
        
        self.assertTrue(success)
        
        # Verify data was stored correctly
        stored_position = self.rt.get_position_data()
        self.assertIsNotNone(stored_position)
        self.assertAlmostEqual(stored_position.x, 100.0, places=2)
        self.assertAlmostEqual(stored_position.y, 200.0, places=2)
    
    def test_send_attitude_data(self):
        """Test sending attitude data"""
        attitude = AttitudeData(roll=90.0, pitch=-45.0)
        success = self.bc.send_attitude_data(5, attitude)
        
        self.assertTrue(success)
        
        # Verify data was stored correctly
        stored_attitude = self.rt.get_attitude_data()
        self.assertIsNotNone(stored_attitude)
        self.assertAlmostEqual(stored_attitude.roll, 90.0, places=2)
        self.assertAlmostEqual(stored_attitude.pitch, -45.0, places=2)
    
    def test_request_position_data(self):
        """Test requesting position data"""
        # First send data
        position = PositionData(x=150.5, y=75.25)
        self.bc.send_position_data(5, position)
        
        # Then request it back
        received_position = self.bc.request_position_data(5)
        
        self.assertIsNotNone(received_position)
        self.assertAlmostEqual(received_position.x, 150.5, places=2)
        self.assertAlmostEqual(received_position.y, 75.25, places=2)
    
    def test_request_attitude_data(self):
        """Test requesting attitude data"""
        # First send data
        attitude = AttitudeData(roll=180.0, pitch=0.0)
        self.bc.send_attitude_data(5, attitude)
        
        # Then request it back
        received_attitude = self.bc.request_attitude_data(5)
        
        self.assertIsNotNone(received_attitude)
        self.assertAlmostEqual(received_attitude.roll, 180.0, places=2)
        self.assertAlmostEqual(received_attitude.pitch, 0.0, places=2)
    
    def test_invalid_rt_address(self):
        """Test operations with invalid RT address"""
        position = PositionData(x=100.0, y=200.0)
        
        # Try to send to non-existent RT
        success = self.bc.send_position_data(99, position)
        self.assertFalse(success)
        
        # Try to request from non-existent RT
        received = self.bc.request_position_data(99)
        self.assertIsNone(received)
    
    def test_message_history(self):
        """Test message history logging"""
        position = PositionData(x=50.0, y=60.0)
        self.bc.send_position_data(5, position)
        
        self.assertEqual(len(self.bc.message_history), 1)
        
        message = self.bc.message_history[0]
        self.assertEqual(message.command.rt_address, 5)
        self.assertEqual(message.command.subaddress, 1)
        self.assertEqual(len(message.data_words), 2)
        self.assertIsNotNone(message.status)


class TestRemoteTerminal(unittest.TestCase):
    """Test Remote Terminal functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.rt = RemoteTerminal(address=10)
    
    def test_receive_data(self):
        """Test receiving data from BC"""
        data_words = [DataWord(0x1234), DataWord(0x5678)]
        status = self.rt.receive_data(1, data_words)
        
        self.assertFalse(status.message_error)
        self.assertEqual(status.rt_address, 10)
        
        # Verify data was stored
        stored_data = self.rt.subaddress_data.get(1)
        self.assertIsNotNone(stored_data)
        self.assertEqual(len(stored_data), 2)
    
    def test_transmit_data(self):
        """Test transmitting data to BC"""
        # First store some data
        data_words = [DataWord(0xABCD), DataWord(0xEF01)]
        self.rt.receive_data(2, data_words)
        
        # Then transmit it
        transmitted_data, status = self.rt.transmit_data(2, 2)
        
        self.assertFalse(status.message_error)
        self.assertEqual(len(transmitted_data), 2)
        self.assertEqual(transmitted_data[0].data, 0xABCD)
        self.assertEqual(transmitted_data[1].data, 0xEF01)


def demonstrate_extended_scenarios():
    """Demonstrate extended usage scenarios"""
    print("\nExtended MIL-STD-1553B Protocol Scenarios")
    print("=" * 50)
    
    # Create a more complex system with multiple RTs
    bc = BusController()
    
    # Navigation RT
    nav_rt = RemoteTerminal(address=1)
    bc.add_remote_terminal(nav_rt)
    
    # Flight Control RT  
    fc_rt = RemoteTerminal(address=2)
    bc.add_remote_terminal(fc_rt)
    
    # Engine Control RT
    engine_rt = RemoteTerminal(address=3)
    bc.add_remote_terminal(engine_rt)
    
    print("Created system with 3 Remote Terminals:")
    print("  RT 1: Navigation System")
    print("  RT 2: Flight Control System") 
    print("  RT 3: Engine Control System")
    print()
    
    # Scenario 1: Navigation data distribution
    print("Scenario 1: Navigation Data Distribution")
    print("-" * 40)
    
    nav_position = PositionData(x=1234.56, y=-987.65)  # GPS coordinates
    nav_attitude = AttitudeData(roll=5.5, pitch=2.3)    # Aircraft attitude
    
    # Navigation system receives GPS data
    bc.send_position_data(1, nav_position)
    bc.send_attitude_data(1, nav_attitude)
    print(f"Sent to NAV RT: Position({nav_position.x}, {nav_position.y})")
    print(f"Sent to NAV RT: Attitude(R={nav_attitude.roll}°, P={nav_attitude.pitch}°)")
    
    # Flight control system gets the same data
    bc.send_position_data(2, nav_position) 
    bc.send_attitude_data(2, nav_attitude)
    print(f"Sent to FC RT: Same navigation data")
    print()
    
    # Scenario 2: Data collection from multiple RTs
    print("Scenario 2: Data Collection from Multiple RTs")
    print("-" * 45)
    
    # Collect position data from all RTs
    for rt_addr, rt_name in [(1, "NAV"), (2, "FC")]:
        position = bc.request_position_data(rt_addr)
        attitude = bc.request_attitude_data(rt_addr)
        
        if position and attitude:
            print(f"Collected from {rt_name} RT:")
            print(f"  Position: X={position.x}, Y={position.y}")
            print(f"  Attitude: Roll={attitude.roll}°, Pitch={attitude.pitch}°")
    print()
    
    # Scenario 3: Error handling
    print("Scenario 3: Error Handling")
    print("-" * 30)
    
    # Try to communicate with non-existent RT
    success = bc.send_position_data(99, nav_position)
    print(f"Send to non-existent RT 99: {'SUCCESS' if success else 'FAILED'}")
    
    data = bc.request_position_data(99)
    print(f"Request from non-existent RT 99: {'SUCCESS' if data else 'FAILED'}")
    print()
    
    # Scenario 4: Performance metrics
    print("Scenario 4: System Performance Metrics")
    print("-" * 38)
    
    total_messages = len(bc.message_history)
    successful_messages = sum(1 for msg in bc.message_history if not msg.status.message_error)
    
    print(f"Total messages transmitted: {total_messages}")
    print(f"Successful transmissions: {successful_messages}")
    print(f"Success rate: {(successful_messages/total_messages)*100:.1f}%")
    
    # Calculate data throughput
    total_data_words = sum(len(msg.data_words) for msg in bc.message_history)
    print(f"Total data words transferred: {total_data_words}")
    print(f"Average data words per message: {total_data_words/total_messages:.1f}")


if __name__ == "__main__":
    # Run unit tests
    print("Running MIL-STD-1553B Protocol Tests...")
    unittest.main(verbosity=2, exit=False)
    
    # Run extended demonstration
    demonstrate_extended_scenarios()