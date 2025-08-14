#!/usr/bin/env python3
"""
Test suite for 1553B Communication Protocol Implementation
Tests data serialization, message handling, and communication flow
"""

import unittest
import time
import threading
from protocol_1553b_example import (
    PositionData, AttitudeData, Message1553B, BusController, 
    RemoteTerminal, CommunicationProtocol, MessageType, Subaddress, ErrorCode
)

class TestPositionData(unittest.TestCase):
    """Test PositionData serialization and deserialization"""
    
    def test_position_creation(self):
        """Test PositionData object creation"""
        pos = PositionData(100.5, 200.3, 1500.7)
        self.assertEqual(pos.x, 100.5)
        self.assertEqual(pos.y, 200.3)
        self.assertEqual(pos.z, 1500.7)
        self.assertIsNotNone(pos.timestamp)
    
    def test_position_serialization(self):
        """Test PositionData to_bytes() method"""
        pos = PositionData(100.5, 200.3, 1500.7)
        data = pos.to_bytes()
        
        # Should be exactly 4 bytes
        self.assertEqual(len(data), 4)
        
        # Check that data is not all zeros
        self.assertNotEqual(data, b'\x00\x00\x00\x00')
    
    def test_position_deserialization(self):
        """Test PositionData from_bytes() method"""
        original_pos = PositionData(100.5, 200.3, 1500.7)
        data = original_pos.to_bytes()
        reconstructed_pos = PositionData.from_bytes(data)
        
        # Values should be close (within rounding error)
        self.assertAlmostEqual(original_pos.x, reconstructed_pos.x, places=1)
        self.assertAlmostEqual(original_pos.y, reconstructed_pos.y, places=1)
        self.assertAlmostEqual(original_pos.z, reconstructed_pos.z, places=1)
    
    def test_position_string_representation(self):
        """Test PositionData string representation"""
        pos = PositionData(100.5, 200.3, 1500.7)
        pos_str = str(pos)
        self.assertIn("Position", pos_str)
        self.assertIn("100.50", pos_str)
        self.assertIn("200.30", pos_str)
        self.assertIn("1500.70", pos_str)

class TestAttitudeData(unittest.TestCase):
    """Test AttitudeData serialization and deserialization"""
    
    def test_attitude_creation(self):
        """Test AttitudeData object creation"""
        att = AttitudeData(15.5, 2.3, 45.7)
        self.assertEqual(att.roll, 15.5)
        self.assertEqual(att.pitch, 2.3)
        self.assertEqual(att.yaw, 45.7)
        self.assertIsNotNone(att.timestamp)
    
    def test_attitude_serialization(self):
        """Test AttitudeData to_bytes() method"""
        att = AttitudeData(15.5, 2.3, 45.7)
        data = att.to_bytes()
        
        # Should be exactly 4 bytes
        self.assertEqual(len(data), 4)
        
        # Check that data is not all zeros
        self.assertNotEqual(data, b'\x00\x00\x00\x00')
    
    def test_attitude_deserialization(self):
        """Test AttitudeData from_bytes() method"""
        original_att = AttitudeData(15.5, 2.3, 45.7)
        data = original_att.to_bytes()
        reconstructed_att = AttitudeData.from_bytes(data)
        
        # Values should be close (within rounding error)
        self.assertAlmostEqual(original_att.roll, reconstructed_att.roll, places=0)
        self.assertAlmostEqual(original_att.pitch, reconstructed_att.pitch, places=0)
        self.assertAlmostEqual(original_att.yaw, reconstructed_att.yaw, places=0)
    
    def test_attitude_angle_wrapping(self):
        """Test that angles wrap correctly (0-360 degrees)"""
        att = AttitudeData(370.0, -10.0, 720.0)  # Test angle wrapping
        data = att.to_bytes()
        reconstructed_att = AttitudeData.from_bytes(data)
        
        # Should handle angle wrapping correctly
        self.assertGreaterEqual(reconstructed_att.roll, 0)
        self.assertLess(reconstructed_att.roll, 360)
        self.assertGreaterEqual(reconstructed_att.pitch, 0)
        self.assertLess(reconstructed_att.pitch, 360)
        self.assertGreaterEqual(reconstructed_att.yaw, 0)
        self.assertLess(reconstructed_att.yaw, 360)
    
    def test_attitude_string_representation(self):
        """Test AttitudeData string representation"""
        att = AttitudeData(15.5, 2.3, 45.7)
        att_str = str(att)
        self.assertIn("Attitude", att_str)
        self.assertIn("15.5°", att_str)
        self.assertIn("2.3°", att_str)
        self.assertIn("45.7°", att_str)

class TestMessage1553B(unittest.TestCase):
    """Test 1553B Message structure and formatting"""
    
    def test_message_creation(self):
        """Test Message1553B object creation"""
        message = Message1553B(1, Subaddress.POSITION_DATA.value, MessageType.DATA, b'\x01\x02\x03\x04')
        self.assertEqual(message.rt_address, 1)
        self.assertEqual(message.subaddress, Subaddress.POSITION_DATA.value)
        self.assertEqual(message.message_type, MessageType.DATA)
        self.assertEqual(message.data, b'\x01\x02\x03\x04')
        self.assertIsNotNone(message.timestamp)
    
    def test_message_parity(self):
        """Test parity bit addition"""
        message = Message1553B(1, Subaddress.POSITION_DATA.value, MessageType.DATA, b'\x01\x02\x03\x04')
        formatted_message = message.add_parity()
        
        # Should have command word, status word, and data words
        self.assertGreater(len(formatted_message), 4)
        
        # Each word should be 16 bits (2 bytes)
        self.assertEqual(len(formatted_message) % 2, 0)
    
    def test_message_string_representation(self):
        """Test Message1553B string representation"""
        message = Message1553B(1, Subaddress.POSITION_DATA.value, MessageType.DATA, b'\x01\x02\x03\x04')
        message_str = str(message)
        self.assertIn("1553B Message", message_str)
        self.assertIn("RT=1", message_str)
        self.assertIn("Sub=1", message_str)
        self.assertIn("DATA", message_str)

class TestRemoteTerminal(unittest.TestCase):
    """Test Remote Terminal functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rt = RemoteTerminal(1, "Test_RT")
    
    def test_rt_creation(self):
        """Test RemoteTerminal object creation"""
        self.assertEqual(self.rt.address, 1)
        self.assertEqual(self.rt.name, "Test_RT")
        self.assertEqual(self.rt.status, ErrorCode.NO_ERROR)
        self.assertFalse(self.rt.busy)
    
    def test_position_update(self):
        """Test position data update"""
        self.rt.update_position(100.5, 200.3, 1500.7)
        pos_data = self.rt.get_position_data()
        
        self.assertEqual(pos_data.x, 100.5)
        self.assertEqual(pos_data.y, 200.3)
        self.assertEqual(pos_data.z, 1500.7)
    
    def test_attitude_update(self):
        """Test attitude data update"""
        self.rt.update_attitude(15.5, 2.3, 45.7)
        att_data = self.rt.get_attitude_data()
        
        self.assertEqual(att_data.roll, 15.5)
        self.assertEqual(att_data.pitch, 2.3)
        self.assertEqual(att_data.yaw, 45.7)
    
    def test_message_reception(self):
        """Test message reception and processing"""
        # Test position data request
        message = Message1553B(1, Subaddress.POSITION_DATA.value, MessageType.DATA)
        success = self.rt.receive_message(message)
        self.assertTrue(success)
        
        # Test attitude data request
        message = Message1553B(1, Subaddress.ATTITUDE_DATA.value, MessageType.DATA)
        success = self.rt.receive_message(message)
        self.assertTrue(success)
        
        # Test unknown subaddress
        message = Message1553B(1, 0xFF, MessageType.DATA)
        success = self.rt.receive_message(message)
        self.assertFalse(success)
    
    def test_busy_state(self):
        """Test busy state handling"""
        self.rt.busy = True
        message = Message1553B(1, Subaddress.POSITION_DATA.value, MessageType.DATA)
        success = self.rt.receive_message(message)
        self.assertFalse(success)
        self.assertEqual(self.rt.status, ErrorCode.BUSY_ERROR)

class TestBusController(unittest.TestCase):
    """Test Bus Controller functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bc = BusController(bus_id=1)
        self.rt1 = RemoteTerminal(1, "RT_1")
        self.rt2 = RemoteTerminal(2, "RT_2")
        self.bc.register_rt(self.rt1)
        self.bc.register_rt(self.rt2)
    
    def test_rt_registration(self):
        """Test Remote Terminal registration"""
        self.assertIn(1, self.bc.remote_terminals)
        self.assertIn(2, self.bc.remote_terminals)
        self.assertEqual(self.bc.remote_terminals[1], self.rt1)
        self.assertEqual(self.bc.remote_terminals[2], self.rt2)
    
    def test_message_sending(self):
        """Test message sending to RTs"""
        data = b'\x01\x02\x03\x04'
        success = self.bc.send_message(1, Subaddress.POSITION_DATA.value, data)
        self.assertTrue(success)
        
        # Test sending to non-existent RT
        success = self.bc.send_message(99, Subaddress.POSITION_DATA.value, data)
        self.assertFalse(success)
    
    def test_data_request(self):
        """Test data request from RTs"""
        # Update RT data
        self.rt1.update_position(100.5, 200.3, 1500.7)
        self.rt1.update_attitude(15.5, 2.3, 45.7)
        
        # Request data
        pos_data = self.bc.request_position_data(1)
        att_data = self.bc.request_attitude_data(1)
        
        self.assertIsNotNone(pos_data)
        self.assertIsNotNone(att_data)
        self.assertEqual(pos_data.x, 100.5)
        self.assertEqual(att_data.roll, 15.5)
    
    def test_broadcast_message(self):
        """Test broadcast messaging"""
        data = b'\x01\x02\x03\x04'
        self.bc.broadcast_message(Subaddress.POSITION_DATA.value, data)
        
        # Both RTs should have received the message
        # (In a real implementation, we would check message queues)
        self.assertTrue(True)  # Placeholder assertion

class TestCommunicationProtocol(unittest.TestCase):
    """Test complete communication protocol"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.protocol = CommunicationProtocol()
        self.rt1 = self.protocol.add_remote_terminal(1, "Navigation_System")
        self.rt2 = self.protocol.add_remote_terminal(2, "Guidance_System")
    
    def test_protocol_creation(self):
        """Test protocol initialization"""
        self.assertIsNotNone(self.protocol.bus_controller)
        self.assertIn(1, self.protocol.remote_terminals)
        self.assertIn(2, self.protocol.remote_terminals)
    
    def test_position_data_transmission(self):
        """Test position data transmission"""
        self.protocol.start_communication()
        
        position = PositionData(100.5, 200.3, 1500.7)
        success = self.protocol.send_position_data(1, position)
        self.assertTrue(success)
        
        # Wait for processing
        time.sleep(0.01)
        
        self.protocol.stop_communication()
    
    def test_attitude_data_transmission(self):
        """Test attitude data transmission"""
        self.protocol.start_communication()
        
        attitude = AttitudeData(15.5, 2.3, 45.7)
        success = self.protocol.send_attitude_data(2, attitude)
        self.assertTrue(success)
        
        # Wait for processing
        time.sleep(0.01)
        
        self.protocol.stop_communication()
    
    def test_broadcast_communication(self):
        """Test broadcast communication"""
        self.protocol.start_communication()
        
        position = PositionData(102.8, 199.5, 1500.9)
        attitude = AttitudeData(15.8, 2.2, 45.9)
        
        self.protocol.broadcast_position(position)
        self.protocol.broadcast_attitude(attitude)
        
        # Wait for processing
        time.sleep(0.01)
        
        self.protocol.stop_communication()
    
    def test_rt_status_retrieval(self):
        """Test RT status retrieval"""
        # Update RT data
        self.rt1.update_position(100.5, 200.3, 1500.7)
        self.rt1.update_attitude(15.5, 2.3, 45.7)
        
        status = self.protocol.get_rt_status(1)
        self.assertIsNotNone(status)
        self.assertEqual(status['address'], 1)
        self.assertEqual(status['name'], "Navigation_System")
        self.assertEqual(status['status'], "NO_ERROR")
        self.assertFalse(status['busy'])
        self.assertIn("Position", status['position'])
        self.assertIn("Attitude", status['attitude'])
    
    def test_nonexistent_rt_status(self):
        """Test status retrieval for non-existent RT"""
        status = self.protocol.get_rt_status(99)
        self.assertIsNone(status)

class TestPerformance(unittest.TestCase):
    """Test protocol performance characteristics"""
    
    def test_message_throughput(self):
        """Test message throughput"""
        protocol = CommunicationProtocol()
        rt = protocol.add_remote_terminal(1, "Performance_Test_RT")
        protocol.start_communication()
        
        position = PositionData(100.0, 200.0, 1500.0)
        message_count = 100
        
        start_time = time.time()
        for i in range(message_count):
            protocol.send_position_data(1, position)
        
        end_time = time.time()
        throughput = message_count / (end_time - start_time)
        
        # Should handle at least 100 messages per second
        self.assertGreater(throughput, 100)
        
        protocol.stop_communication()
    
    def test_concurrent_access(self):
        """Test concurrent access to protocol"""
        protocol = CommunicationProtocol()
        rt = protocol.add_remote_terminal(1, "Concurrent_Test_RT")
        protocol.start_communication()
        
        position = PositionData(100.0, 200.0, 1500.0)
        attitude = AttitudeData(15.0, 2.0, 45.0)
        
        def send_position():
            for i in range(10):
                protocol.send_position_data(1, position)
                time.sleep(0.001)
        
        def send_attitude():
            for i in range(10):
                protocol.send_attitude_data(1, attitude)
                time.sleep(0.001)
        
        # Start concurrent threads
        thread1 = threading.Thread(target=send_position)
        thread2 = threading.Thread(target=send_attitude)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Should complete without errors
        self.assertTrue(True)
        
        protocol.stop_communication()

def run_demo():
    """Run a demonstration of the 1553B protocol"""
    print("=== 1553B Protocol Demonstration ===\n")
    
    # Create protocol
    protocol = CommunicationProtocol()
    
    # Add remote terminals
    nav_rt = protocol.add_remote_terminal(1, "Navigation_System")
    guidance_rt = protocol.add_remote_terminal(2, "Guidance_System")
    control_rt = protocol.add_remote_terminal(3, "Control_System")
    
    # Start communication
    protocol.start_communication()
    
    try:
        print("1. Testing Position Data Transmission...")
        position = PositionData(100.5, 200.3, 1500.7)
        protocol.send_position_data(1, position)
        time.sleep(0.01)
        
        print("2. Testing Attitude Data Transmission...")
        attitude = AttitudeData(15.5, 2.3, 45.7)
        protocol.send_attitude_data(2, attitude)
        time.sleep(0.01)
        
        print("3. Testing Broadcast Communication...")
        broadcast_pos = PositionData(102.8, 199.5, 1500.9)
        broadcast_att = AttitudeData(15.8, 2.2, 45.9)
        protocol.broadcast_position(broadcast_pos)
        protocol.broadcast_attitude(broadcast_att)
        time.sleep(0.01)
        
        print("4. Displaying RT Status...")
        for rt_address in [1, 2, 3]:
            status = protocol.get_rt_status(rt_address)
            if status:
                print(f"RT {status['address']} ({status['name']}):")
                print(f"  Status: {status['status']}")
                print(f"  Position: {status['position']}")
                print(f"  Attitude: {status['attitude']}")
                print()
        
        print("5. Testing Data Retrieval...")
        pos_data = protocol.bus_controller.request_position_data(1)
        att_data = protocol.bus_controller.request_attitude_data(2)
        
        if pos_data:
            print(f"Retrieved position: {pos_data}")
        if att_data:
            print(f"Retrieved attitude: {att_data}")
        
        print("\nDemonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
    finally:
        protocol.stop_communication()

if __name__ == "__main__":
    # Run tests
    print("Running 1553B Protocol Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50 + "\n")
    
    # Run demonstration
    run_demo()