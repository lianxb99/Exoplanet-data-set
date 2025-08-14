#!/usr/bin/env python3
"""
1553B Communication Protocol Implementation
Military Standard 1553B (MIL-STD-1553B) Digital Time Division Command/Response Multiplex Data Bus

This implementation demonstrates:
- Message structure and formatting
- Position and attitude data handling
- Bus Controller (BC) and Remote Terminal (RT) communication
- Error detection and handling
- Real-time data transmission
"""

import struct
import time
import threading
from enum import Enum
from typing import List, Tuple, Optional, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """1553B Message Types"""
    COMMAND = 0x00
    STATUS = 0x01
    DATA = 0x02
    MODE_CODE = 0x03

class Subaddress(Enum):
    """Remote Terminal Subaddresses"""
    POSITION_DATA = 0x01
    ATTITUDE_DATA = 0x02
    STATUS_DATA = 0x03
    COMMAND_DATA = 0x04

class ErrorCode(Enum):
    """1553B Error Codes"""
    NO_ERROR = 0x00
    PARITY_ERROR = 0x01
    SYNC_ERROR = 0x02
    WORD_COUNT_ERROR = 0x03
    TIMEOUT_ERROR = 0x04
    BUSY_ERROR = 0x05
    SUBSYSTEM_ERROR = 0x06

class PositionData:
    """Position data structure (4 bytes)"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x  # X coordinate (meters)
        self.y = y  # Y coordinate (meters)
        self.z = z  # Z coordinate (meters)
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Convert position data to 4-byte format"""
        # Pack as 3 coordinates (1 byte each) + 1 byte for flags
        # Scale coordinates to fit in 1 byte each (0-255 range)
        # Assuming position range of 0-2550 meters (scaled by 10)
        x_byte = min(255, max(0, int(self.x / 10)))  # Scale by 10, clamp to 0-255
        y_byte = min(255, max(0, int(self.y / 10)))
        z_byte = min(255, max(0, int(self.z / 10)))
        flags = 0x00  # Status flags
        
        return bytes([x_byte, y_byte, z_byte, flags])
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'PositionData':
        """Create PositionData from 4-byte format"""
        if len(data) != 4:
            raise ValueError(f"Position data must be 4 bytes, got {len(data)}")
        
        x = data[0] * 10.0  # Scale back by 10
        y = data[1] * 10.0
        z = data[2] * 10.0
        
        return cls(x, y, z)
    
    def __str__(self) -> str:
        return f"Position(x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f})"

class AttitudeData:
    """Attitude data structure (4 bytes)"""
    def __init__(self, roll: float, pitch: float, yaw: float):
        self.roll = roll   # Roll angle (degrees)
        self.pitch = pitch # Pitch angle (degrees)
        self.yaw = yaw     # Yaw angle (degrees)
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Convert attitude data to 4-byte format"""
        # Pack as 3 angles (1 byte each) + 1 byte for flags
        # Each angle is scaled to 0-255 range (0-360 degrees)
        roll_byte = int((self.roll % 360) * 255 / 360)
        pitch_byte = int((self.pitch % 360) * 255 / 360)
        yaw_byte = int((self.yaw % 360) * 255 / 360)
        flags = 0x00  # Status flags
        
        return bytes([roll_byte, pitch_byte, yaw_byte, flags])
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'AttitudeData':
        """Create AttitudeData from 4-byte format"""
        if len(data) != 4:
            raise ValueError(f"Attitude data must be 4 bytes, got {len(data)}")
        
        roll = (data[0] * 360) / 255
        pitch = (data[1] * 360) / 255
        yaw = (data[2] * 360) / 255
        
        return cls(roll, pitch, yaw)
    
    def __str__(self) -> str:
        return f"Attitude(roll={self.roll:.1f}°, pitch={self.pitch:.1f}°, yaw={self.yaw:.1f}°)"

class Message1553B:
    """1553B Message Structure"""
    def __init__(self, rt_address: int, subaddress: int, message_type: MessageType, data: bytes = b''):
        self.rt_address = rt_address      # Remote Terminal Address (5 bits)
        self.subaddress = subaddress      # Subaddress (5 bits)
        self.message_type = message_type  # Message Type
        self.data = data                  # Message Data
        self.timestamp = time.time()
        self.sequence_number = 0
        
    def add_parity(self) -> bytes:
        """Add parity bit to each word (odd parity)"""
        def add_parity_bit(word: int) -> int:
            # Count set bits
            bit_count = bin(word & 0x1F).count('1')  # Only lower 5 bits
            # Add parity bit (odd parity)
            if bit_count % 2 == 0:
                return word | 0x20  # Set bit 5
            else:
                return word & 0x1F  # Clear bit 5
        
        # Command word: RT Address (5 bits) + T/R (1 bit) + Subaddress (5 bits) + Word Count (5 bits)
        command_word = (self.rt_address << 11) | (0x01 << 10) | (self.subaddress << 5) | len(self.data)
        command_word = add_parity_bit(command_word)
        
        # Status word: RT Address (5 bits) + Status bits (10 bits)
        status_word = (self.rt_address << 11) | 0x000  # Simplified status
        status_word = add_parity_bit(status_word)
        
        # Data words with parity
        data_words = []
        for i in range(0, len(self.data), 2):
            word_data = self.data[i:i+2]
            if len(word_data) == 1:
                word_data += b'\x00'  # Pad with zero
            word = int.from_bytes(word_data, byteorder='big')
            word = add_parity_bit(word)
            data_words.append(word)
        
        # Construct message
        message = struct.pack('>H', command_word)  # Command word
        message += struct.pack('>H', status_word)   # Status word
        for word in data_words:
            message += struct.pack('>H', word)
        
        return message
    
    def __str__(self) -> str:
        return f"1553B Message: RT={self.rt_address}, Sub={self.subaddress}, Type={self.message_type.name}, Data={len(self.data)} bytes"

class BusController:
    """1553B Bus Controller - Manages communication on the bus"""
    def __init__(self, bus_id: int = 1):
        self.bus_id = bus_id
        self.remote_terminals: Dict[int, 'RemoteTerminal'] = {}
        self.message_queue: List[Message1553B] = []
        self.sequence_counter = 0
        self.running = False
        self.lock = threading.Lock()
        
    def register_rt(self, rt: 'RemoteTerminal'):
        """Register a Remote Terminal"""
        self.remote_terminals[rt.address] = rt
        logger.info(f"Registered RT {rt.address} on bus {self.bus_id}")
    
    def send_message(self, rt_address: int, subaddress: int, data: bytes) -> bool:
        """Send a message to a specific RT"""
        if rt_address not in self.remote_terminals:
            logger.error(f"RT {rt_address} not found on bus {self.bus_id}")
            return False
        
        message = Message1553B(rt_address, subaddress, MessageType.DATA, data)
        message.sequence_number = self.sequence_counter
        self.sequence_counter += 1
        
        with self.lock:
            self.message_queue.append(message)
        
        logger.info(f"Queued message for RT {rt_address}, subaddress {subaddress}")
        return True
    
    def request_position_data(self, rt_address: int) -> Optional[PositionData]:
        """Request position data from RT"""
        if rt_address not in self.remote_terminals:
            return None
        
        rt = self.remote_terminals[rt_address]
        return rt.get_position_data()
    
    def request_attitude_data(self, rt_address: int) -> Optional[AttitudeData]:
        """Request attitude data from RT"""
        if rt_address not in self.remote_terminals:
            return None
        
        rt = self.remote_terminals[rt_address]
        return rt.get_attitude_data()
    
    def broadcast_message(self, subaddress: int, data: bytes):
        """Broadcast message to all RTs"""
        for rt_address in self.remote_terminals:
            self.send_message(rt_address, subaddress, data)
    
    def start(self):
        """Start the bus controller"""
        self.running = True
        logger.info(f"Bus Controller {self.bus_id} started")
        
        # Start message processing thread
        self.processing_thread = threading.Thread(target=self._process_messages)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop(self):
        """Stop the bus controller"""
        self.running = False
        logger.info(f"Bus Controller {self.bus_id} stopped")
    
    def _process_messages(self):
        """Process queued messages"""
        while self.running:
            with self.lock:
                if self.message_queue:
                    message = self.message_queue.pop(0)
                    
                    # Simulate message transmission
                    rt = self.remote_terminals.get(message.rt_address)
                    if rt:
                        success = rt.receive_message(message)
                        if success:
                            logger.info(f"Message sent successfully to RT {message.rt_address}")
                        else:
                            logger.warning(f"Message failed to RT {message.rt_address}")
            
            time.sleep(0.001)  # 1ms cycle time

class RemoteTerminal:
    """1553B Remote Terminal - Responds to bus controller commands"""
    def __init__(self, address: int, name: str = ""):
        self.address = address
        self.name = name or f"RT_{address}"
        self.position_data = PositionData(0.0, 0.0, 0.0)
        self.attitude_data = AttitudeData(0.0, 0.0, 0.0)
        self.status = ErrorCode.NO_ERROR
        self.busy = False
        self.last_update = time.time()
        
    def update_position(self, x: float, y: float, z: float):
        """Update position data"""
        self.position_data = PositionData(x, y, z)
        self.last_update = time.time()
        logger.debug(f"{self.name}: Position updated to {self.position_data}")
    
    def update_attitude(self, roll: float, pitch: float, yaw: float):
        """Update attitude data"""
        self.attitude_data = AttitudeData(roll, pitch, yaw)
        self.last_update = time.time()
        logger.debug(f"{self.name}: Attitude updated to {self.attitude_data}")
    
    def get_position_data(self) -> PositionData:
        """Get current position data"""
        return self.position_data
    
    def get_attitude_data(self) -> AttitudeData:
        """Get current attitude data"""
        return self.attitude_data
    
    def receive_message(self, message: Message1553B) -> bool:
        """Receive and process a message from the bus controller"""
        if self.busy:
            self.status = ErrorCode.BUSY_ERROR
            return False
        
        try:
            if message.subaddress == Subaddress.POSITION_DATA.value:
                # Handle position data request
                response_data = self.position_data.to_bytes()
                logger.info(f"{self.name}: Position data requested")
                return True
                
            elif message.subaddress == Subaddress.ATTITUDE_DATA.value:
                # Handle attitude data request
                response_data = self.attitude_data.to_bytes()
                logger.info(f"{self.name}: Attitude data requested")
                return True
                
            elif message.subaddress == Subaddress.STATUS_DATA.value:
                # Handle status request
                logger.info(f"{self.name}: Status requested")
                return True
                
            else:
                logger.warning(f"{self.name}: Unknown subaddress {message.subaddress}")
                return False
                
        except Exception as e:
            logger.error(f"{self.name}: Error processing message: {e}")
            self.status = ErrorCode.SUBSYSTEM_ERROR
            return False

class CommunicationProtocol:
    """Main 1553B Communication Protocol Implementation"""
    def __init__(self):
        self.bus_controller = BusController(bus_id=1)
        self.remote_terminals = {}
        self.running = False
        
    def add_remote_terminal(self, address: int, name: str = "") -> RemoteTerminal:
        """Add a remote terminal to the system"""
        rt = RemoteTerminal(address, name)
        self.remote_terminals[address] = rt
        self.bus_controller.register_rt(rt)
        return rt
    
    def start_communication(self):
        """Start the communication system"""
        self.bus_controller.start()
        self.running = True
        logger.info("1553B Communication Protocol started")
    
    def stop_communication(self):
        """Stop the communication system"""
        self.bus_controller.stop()
        self.running = False
        logger.info("1553B Communication Protocol stopped")
    
    def send_position_data(self, rt_address: int, position: PositionData):
        """Send position data to a specific RT"""
        data = position.to_bytes()
        success = self.bus_controller.send_message(rt_address, Subaddress.POSITION_DATA.value, data)
        if success:
            logger.info(f"Position data sent to RT {rt_address}: {position}")
        return success
    
    def send_attitude_data(self, rt_address: int, attitude: AttitudeData):
        """Send attitude data to a specific RT"""
        data = attitude.to_bytes()
        success = self.bus_controller.send_message(rt_address, Subaddress.ATTITUDE_DATA.value, data)
        if success:
            logger.info(f"Attitude data sent to RT {rt_address}: {attitude}")
        return success
    
    def broadcast_position(self, position: PositionData):
        """Broadcast position data to all RTs"""
        data = position.to_bytes()
        self.bus_controller.broadcast_message(Subaddress.POSITION_DATA.value, data)
        logger.info(f"Position data broadcasted: {position}")
    
    def broadcast_attitude(self, attitude: AttitudeData):
        """Broadcast attitude data to all RTs"""
        data = attitude.to_bytes()
        self.bus_controller.broadcast_message(Subaddress.ATTITUDE_DATA.value, data)
        logger.info(f"Attitude data broadcasted: {attitude}")
    
    def get_rt_status(self, rt_address: int) -> Optional[Dict]:
        """Get status of a specific RT"""
        if rt_address not in self.remote_terminals:
            return None
        
        rt = self.remote_terminals[rt_address]
        return {
            'address': rt.address,
            'name': rt.name,
            'status': rt.status.name,
            'busy': rt.busy,
            'last_update': rt.last_update,
            'position': str(rt.position_data),
            'attitude': str(rt.attitude_data)
        }

def main():
    """Example usage of the 1553B Communication Protocol"""
    print("=== 1553B Communication Protocol Example ===\n")
    
    # Create communication protocol
    protocol = CommunicationProtocol()
    
    # Add remote terminals
    rt1 = protocol.add_remote_terminal(1, "Navigation_System")
    rt2 = protocol.add_remote_terminal(2, "Guidance_System")
    rt3 = protocol.add_remote_terminal(3, "Control_System")
    
    # Start communication
    protocol.start_communication()
    
    try:
        # Simulate data updates
        print("Simulating position and attitude data transmission...\n")
        
        # Update position data
        position1 = PositionData(100.5, 200.3, 1500.7)
        position2 = PositionData(105.2, 198.8, 1501.2)
        
        # Update attitude data
        attitude1 = AttitudeData(15.5, 2.3, 45.7)
        attitude2 = AttitudeData(16.2, 2.1, 46.1)
        
        # Send data to specific RTs
        protocol.send_position_data(1, position1)
        protocol.send_attitude_data(1, attitude1)
        
        protocol.send_position_data(2, position2)
        protocol.send_attitude_data(2, attitude2)
        
        # Broadcast data to all RTs
        broadcast_position = PositionData(102.8, 199.5, 1500.9)
        broadcast_attitude = AttitudeData(15.8, 2.2, 45.9)
        
        protocol.broadcast_position(broadcast_position)
        protocol.broadcast_attitude(broadcast_attitude)
        
        # Wait for processing
        time.sleep(0.1)
        
        # Display RT status
        print("Remote Terminal Status:")
        print("-" * 50)
        for rt_address in [1, 2, 3]:
            status = protocol.get_rt_status(rt_address)
            if status:
                print(f"RT {status['address']} ({status['name']}):")
                print(f"  Status: {status['status']}")
                print(f"  Busy: {status['busy']}")
                print(f"  Position: {status['position']}")
                print(f"  Attitude: {status['attitude']}")
                print()
        
        # Demonstrate data retrieval
        print("Data Retrieval Example:")
        print("-" * 30)
        pos_data = protocol.bus_controller.request_position_data(1)
        att_data = protocol.bus_controller.request_attitude_data(1)
        
        if pos_data:
            print(f"Retrieved position from RT 1: {pos_data}")
        if att_data:
            print(f"Retrieved attitude from RT 1: {att_data}")
        
    except KeyboardInterrupt:
        print("\nStopping communication...")
    finally:
        protocol.stop_communication()
        print("Communication stopped.")

if __name__ == "__main__":
    main()