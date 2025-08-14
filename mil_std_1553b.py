#!/usr/bin/env python3
"""
MIL-STD-1553B Communication Protocol Implementation
==================================================

This implementation demonstrates a complete MIL-STD-1553B protocol
for transmitting position and attitude data between a Bus Controller (BC)
and Remote Terminals (RTs).

Example: 4 bytes position data + 4 bytes attitude data = 4 data words (16-bit each)
"""

import struct
import time
from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass


class MessageType(Enum):
    """1553B Message Types"""
    BC_TO_RT = 0  # Bus Controller to Remote Terminal
    RT_TO_BC = 1  # Remote Terminal to Bus Controller
    RT_TO_RT = 2  # Remote Terminal to Remote Terminal
    MODE_COMMAND = 3  # Mode Command


class SyncPattern(Enum):
    """1553B Sync Patterns (3-bit patterns)"""
    COMMAND_SYNC = 0b100    # Command word sync
    DATA_SYNC = 0b000       # Data word sync
    STATUS_SYNC = 0b100     # Status word sync (same as command)


@dataclass
class PositionData:
    """Position data structure (4 bytes total)"""
    x: float  # X coordinate (2 bytes when packed)
    y: float  # Y coordinate (2 bytes when packed)
    
    def to_bytes(self) -> bytes:
        """Convert position to 4 bytes (2 int16 values)"""
        # Scale floats and pack as signed int16 values
        x_int = max(-32768, min(32767, int(self.x * 100)))  # Clamp to int16 range
        y_int = max(-32768, min(32767, int(self.y * 100)))  # Clamp to int16 range
        return struct.pack('>hh', x_int, y_int)  # Big-endian 2x signed int16
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'PositionData':
        """Create PositionData from 4 bytes"""
        x_int, y_int = struct.unpack('>hh', data)  # Unpack as signed int16
        return cls(x=x_int / 100.0, y=y_int / 100.0)


@dataclass
class AttitudeData:
    """Attitude data structure (4 bytes total)"""
    roll: float   # Roll angle (2 bytes when packed)
    pitch: float  # Pitch angle (2 bytes when packed)
    
    def to_bytes(self) -> bytes:
        """Convert attitude to 4 bytes (2 int16 values)"""
        # Scale angles and pack as signed int16 values
        roll_int = max(-32768, min(32767, int(self.roll * 100)))  # Clamp to int16 range
        pitch_int = max(-32768, min(32767, int(self.pitch * 100)))  # Clamp to int16 range
        return struct.pack('>hh', roll_int, pitch_int)  # Big-endian 2x signed int16
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'AttitudeData':
        """Create AttitudeData from 4 bytes"""
        roll_int, pitch_int = struct.unpack('>hh', data)  # Unpack as signed int16
        return cls(roll=roll_int / 100.0, pitch=pitch_int / 100.0)


class Word1553B:
    """Base class for 1553B words (20 bits total: 3-bit sync + 16-bit data + 1-bit parity)"""
    
    def __init__(self, sync: int, data: int):
        self.sync = sync & 0x7        # 3 bits
        self.data = data & 0xFFFF     # 16 bits
        self.parity = self._calculate_parity()
    
    def _calculate_parity(self) -> int:
        """Calculate odd parity for the data word"""
        count = bin(self.data).count('1')
        return 1 if count % 2 == 0 else 0  # Odd parity
    
    def to_bytes(self) -> bytes:
        """Convert word to bytes for transmission"""
        # Pack as 32-bit value: sync(3) + data(16) + parity(1) + padding(12)
        word = (self.sync << 17) | (self.data << 1) | self.parity
        return struct.pack('>I', word)
    
    def __repr__(self):
        return f"Word1553B(sync=0b{self.sync:03b}, data=0x{self.data:04X}, parity={self.parity})"


class CommandWord(Word1553B):
    """1553B Command Word structure"""
    
    def __init__(self, rt_address: int, tr_bit: int, subaddress: int, word_count: int):
        self.rt_address = rt_address & 0x1F    # 5 bits (0-31)
        self.tr_bit = tr_bit & 0x1             # 1 bit (0=receive, 1=transmit)
        self.subaddress = subaddress & 0x1F    # 5 bits (0-31)
        self.word_count = word_count & 0x1F    # 5 bits (0-31, 0 means 32 words)
        
        # Build 16-bit command word
        data = (self.rt_address << 11) | (self.tr_bit << 10) | (self.subaddress << 5) | self.word_count
        super().__init__(SyncPattern.COMMAND_SYNC.value, data)
    
    def __repr__(self):
        return (f"CommandWord(RT={self.rt_address}, T/R={'T' if self.tr_bit else 'R'}, "
                f"SA={self.subaddress}, WC={self.word_count})")


class StatusWord(Word1553B):
    """1553B Status Word structure"""
    
    def __init__(self, rt_address: int, message_error: bool = False, 
                 instrumentation: bool = False, service_request: bool = False,
                 broadcast_received: bool = False, busy: bool = False,
                 subsystem_flag: bool = False, dynamic_bus_control: bool = False,
                 terminal_flag: bool = False):
        
        self.rt_address = rt_address & 0x1F
        self.message_error = message_error
        self.instrumentation = instrumentation  
        self.service_request = service_request
        self.broadcast_received = broadcast_received
        self.busy = busy
        self.subsystem_flag = subsystem_flag
        self.dynamic_bus_control = dynamic_bus_control
        self.terminal_flag = terminal_flag
        
        # Build 16-bit status word
        data = (self.rt_address << 11)
        if message_error: data |= (1 << 10)
        if instrumentation: data |= (1 << 9)
        if service_request: data |= (1 << 8)
        if broadcast_received: data |= (1 << 4)
        if busy: data |= (1 << 3)
        if subsystem_flag: data |= (1 << 2)
        if dynamic_bus_control: data |= (1 << 1)
        if terminal_flag: data |= 1
        
        super().__init__(SyncPattern.STATUS_SYNC.value, data)


class DataWord(Word1553B):
    """1553B Data Word structure"""
    
    def __init__(self, data: int):
        super().__init__(SyncPattern.DATA_SYNC.value, data)


class Message1553B:
    """Complete 1553B message"""
    
    def __init__(self, command: CommandWord, data_words: List[DataWord] = None, 
                 status: StatusWord = None):
        self.command = command
        self.data_words = data_words or []
        self.status = status
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Serialize complete message to bytes"""
        message_bytes = self.command.to_bytes()
        
        # Add data words if this is a transmit operation
        if self.command.tr_bit == 0:  # Receive command (BC->RT)
            for data_word in self.data_words:
                message_bytes += data_word.to_bytes()
        
        # Add status word if present
        if self.status:
            message_bytes += self.status.to_bytes()
            
        return message_bytes


class RemoteTerminal:
    """1553B Remote Terminal implementation"""
    
    def __init__(self, address: int):
        self.address = address
        self.subaddress_data = {}  # Storage for different subaddresses
        self.busy = False
        self.last_message_time = 0
    
    def receive_data(self, subaddress: int, data_words: List[DataWord]) -> StatusWord:
        """Receive data from Bus Controller"""
        try:
            # Store data words in the specified subaddress
            self.subaddress_data[subaddress] = data_words
            self.last_message_time = time.time()
            
            # Return successful status
            return StatusWord(self.address)
            
        except Exception:
            # Return error status
            return StatusWord(self.address, message_error=True)
    
    def transmit_data(self, subaddress: int, word_count: int) -> Tuple[List[DataWord], StatusWord]:
        """Transmit data to Bus Controller"""
        try:
            # Get data from specified subaddress
            data_words = self.subaddress_data.get(subaddress, [])
            
            # Limit to requested word count
            if len(data_words) > word_count:
                data_words = data_words[:word_count]
            
            status = StatusWord(self.address)
            return data_words, status
            
        except Exception:
            return [], StatusWord(self.address, message_error=True)
    
    def get_position_data(self) -> Optional[PositionData]:
        """Get position data from subaddress 1"""
        data_words = self.subaddress_data.get(1, [])
        if len(data_words) >= 2:
            # Combine two 16-bit words into 4 bytes
            bytes_data = struct.pack('>HH', data_words[0].data, data_words[1].data)
            return PositionData.from_bytes(bytes_data)
        return None
    
    def get_attitude_data(self) -> Optional[AttitudeData]:
        """Get attitude data from subaddress 2"""
        data_words = self.subaddress_data.get(2, [])
        if len(data_words) >= 2:
            # Combine two 16-bit words into 4 bytes
            bytes_data = struct.pack('>HH', data_words[0].data, data_words[1].data)
            return AttitudeData.from_bytes(bytes_data)
        return None


class BusController:
    """1553B Bus Controller implementation"""
    
    def __init__(self):
        self.remote_terminals = {}
        self.message_history = []
    
    def add_remote_terminal(self, rt: RemoteTerminal):
        """Add a Remote Terminal to the bus"""
        self.remote_terminals[rt.address] = rt
    
    def send_position_data(self, rt_address: int, position: PositionData) -> bool:
        """Send position data to specific RT (subaddress 1)"""
        if rt_address not in self.remote_terminals:
            return False
        
        rt = self.remote_terminals[rt_address]
        
        # Convert position data to data words (2 words for 4 bytes)
        pos_bytes = position.to_bytes()
        word1_data, word2_data = struct.unpack('>HH', pos_bytes)  # Read as unsigned for data words
        
        data_words = [DataWord(word1_data), DataWord(word2_data)]
        
        # Create command word for BC->RT transfer to subaddress 1
        command = CommandWord(rt_address, tr_bit=0, subaddress=1, word_count=2)
        
        # Send message
        status = rt.receive_data(1, data_words)
        
        # Log message
        message = Message1553B(command, data_words, status)
        self.message_history.append(message)
        
        return not status.message_error
    
    def send_attitude_data(self, rt_address: int, attitude: AttitudeData) -> bool:
        """Send attitude data to specific RT (subaddress 2)"""
        if rt_address not in self.remote_terminals:
            return False
        
        rt = self.remote_terminals[rt_address]
        
        # Convert attitude data to data words (2 words for 4 bytes)
        att_bytes = attitude.to_bytes()
        word1_data, word2_data = struct.unpack('>HH', att_bytes)  # Read as unsigned for data words
        
        data_words = [DataWord(word1_data), DataWord(word2_data)]
        
        # Create command word for BC->RT transfer to subaddress 2
        command = CommandWord(rt_address, tr_bit=0, subaddress=2, word_count=2)
        
        # Send message
        status = rt.receive_data(2, data_words)
        
        # Log message
        message = Message1553B(command, data_words, status)
        self.message_history.append(message)
        
        return not status.message_error
    
    def request_position_data(self, rt_address: int) -> Optional[PositionData]:
        """Request position data from specific RT (subaddress 1)"""
        if rt_address not in self.remote_terminals:
            return None
        
        rt = self.remote_terminals[rt_address]
        
        # Create command word for RT->BC transfer from subaddress 1
        command = CommandWord(rt_address, tr_bit=1, subaddress=1, word_count=2)
        
        # Request data
        data_words, status = rt.transmit_data(1, 2)
        
        # Log message
        message = Message1553B(command, data_words, status)
        self.message_history.append(message)
        
        if not status.message_error and len(data_words) >= 2:
            # Convert data words back to position data
            bytes_data = struct.pack('>HH', data_words[0].data, data_words[1].data)
            return PositionData.from_bytes(bytes_data)
        
        return None
    
    def request_attitude_data(self, rt_address: int) -> Optional[AttitudeData]:
        """Request attitude data from specific RT (subaddress 2)"""
        if rt_address not in self.remote_terminals:
            return None
        
        rt = self.remote_terminals[rt_address]
        
        # Create command word for RT->BC transfer from subaddress 2
        command = CommandWord(rt_address, tr_bit=1, subaddress=2, word_count=2)
        
        # Request data
        data_words, status = rt.transmit_data(2, 2)
        
        # Log message
        message = Message1553B(command, data_words, status)
        self.message_history.append(message)
        
        if not status.message_error and len(data_words) >= 2:
            # Convert data words back to attitude data
            bytes_data = struct.pack('>HH', data_words[0].data, data_words[1].data)
            return AttitudeData.from_bytes(bytes_data)
        
        return None


def demonstrate_1553b_protocol():
    """Demonstrate complete 1553B communication protocol"""
    print("MIL-STD-1553B Communication Protocol Demonstration")
    print("=" * 55)
    
    # Create Bus Controller
    bc = BusController()
    
    # Create Remote Terminal
    rt = RemoteTerminal(address=3)
    bc.add_remote_terminal(rt)
    
    # Create sample data
    position = PositionData(x=123.45, y=267.89)  # Keep Y within int16 range when scaled
    attitude = AttitudeData(roll=15.5, pitch=-10.25)
    
    print(f"Original Position Data: X={position.x}, Y={position.y}")
    print(f"Original Attitude Data: Roll={attitude.roll}°, Pitch={attitude.pitch}°")
    print()
    
    # Send position data
    print("1. Sending Position Data (BC -> RT)")
    success = bc.send_position_data(3, position)
    print(f"   Status: {'SUCCESS' if success else 'FAILED'}")
    
    # Send attitude data
    print("2. Sending Attitude Data (BC -> RT)")
    success = bc.send_attitude_data(3, attitude)
    print(f"   Status: {'SUCCESS' if success else 'FAILED'}")
    print()
    
    # Request data back
    print("3. Requesting Position Data (RT -> BC)")
    received_position = bc.request_position_data(3)
    if received_position:
        print(f"   Received: X={received_position.x}, Y={received_position.y}")
    else:
        print("   FAILED to receive position data")
    
    print("4. Requesting Attitude Data (RT -> BC)")
    received_attitude = bc.request_attitude_data(3)
    if received_attitude:
        print(f"   Received: Roll={received_attitude.roll}°, Pitch={received_attitude.pitch}°")
    else:
        print("   FAILED to receive attitude data")
    print()
    
    # Display message history
    print("Message History:")
    print("-" * 40)
    for i, msg in enumerate(bc.message_history, 1):
        print(f"{i}. {msg.command}")
        if msg.data_words:
            print(f"   Data Words: {len(msg.data_words)} words")
            for j, dw in enumerate(msg.data_words):
                print(f"     Word {j+1}: 0x{dw.data:04X}")
        if msg.status:
            error_status = "ERROR" if msg.status.message_error else "OK"
            print(f"   Status: RT {msg.status.rt_address} - {error_status}")
        print()


if __name__ == "__main__":
    demonstrate_1553b_protocol()