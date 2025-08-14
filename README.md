# MIL-STD-1553B Communication Protocol Implementation

This repository provides a complete, working implementation of the MIL-STD-1553B communication protocol specifically designed for handling 4 bytes of position data and 4 bytes of attitude data in avionic systems.

## 🎯 Overview

MIL-STD-1553B is a military standard that defines a time-division multiplexed data bus for reliable communication between avionic systems. This implementation demonstrates how to structure and transmit position and attitude data according to the protocol specification.

## 📁 Files

- **`mil_std_1553b.py`** - Complete protocol implementation
- **`test_1553b_protocol.py`** - Comprehensive test suite
- **`1553B_Protocol_Guide.md`** - Detailed technical documentation
- **`README.md`** - This file

## 🚀 Quick Start

```bash
# Run the basic demonstration
python3 mil_std_1553b.py

# Run comprehensive tests
python3 test_1553b_protocol.py
```

## 💡 Key Features

### ✅ Standards Compliant
- Follows MIL-STD-1553B specification
- Proper word structure (20-bit words with sync, data, parity)
- Correct command/response protocol implementation

### ✅ Data Handling
- **Position Data**: 4 bytes (X,Y coordinates) → 2 data words
- **Attitude Data**: 4 bytes (Roll,Pitch angles) → 2 data words
- Automatic scaling and packing for transmission
- Error detection and correction

### ✅ Protocol Components
- **Bus Controller (BC)**: Manages all communication
- **Remote Terminals (RTs)**: Respond to BC commands
- **Message Types**: Command, Data, and Status words
- **Subaddresses**: Organized data storage (Position=1, Attitude=2)

## 🔧 Usage Example

```python
from mil_std_1553b import BusController, RemoteTerminal, PositionData, AttitudeData

# Create system components
bc = BusController()
rt = RemoteTerminal(address=3)
bc.add_remote_terminal(rt)

# Create data (4 bytes each)
position = PositionData(x=123.45, y=267.89)  # 4 bytes total
attitude = AttitudeData(roll=15.5, pitch=-10.25)  # 4 bytes total

# Send data (BC → RT)
bc.send_position_data(3, position)    # Subaddress 1
bc.send_attitude_data(3, attitude)    # Subaddress 2

# Request data (RT → BC)
received_pos = bc.request_position_data(3)
received_att = bc.request_attitude_data(3)

print(f"Position: X={received_pos.x}, Y={received_pos.y}")
print(f"Attitude: Roll={received_att.roll}°, Pitch={received_att.pitch}°")
```

## 📊 Communication Flow

### Sending Position Data (BC → RT)

```
1. BC creates Command Word:
   ┌─────────────────────────────────────────────────────────┐
   │ RT Addr │ T/R │ Subaddr │ Word Count │ Sync │ Parity   │
   │   (5)   │ (1) │   (5)   │    (5)     │ (3)  │   (1)    │
   │    3    │  0  │    1    │     2      │ 100  │    X     │
   └─────────────────────────────────────────────────────────┘

2. BC sends 2 Data Words:
   Data Word 1: X coordinate (scaled to int16)
   Data Word 2: Y coordinate (scaled to int16)

3. RT responds with Status Word:
   ┌─────────────────────────────────────────────────────────┐
   │ RT Addr │ Status Flags (10 bits)   │ Sync │ Parity    │
   │   (5)   │ ME│IN│SR│3│BC│BU│SS│DB│TF│ (3)  │   (1)     │
   │    3    │ 0 │0 │0 │0│0 │0 │0 │0 │0 │ 100  │    X      │
   └─────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

### Data Structures
```python
@dataclass
class PositionData:
    x: float  # X coordinate (2 bytes when packed)
    y: float  # Y coordinate (2 bytes when packed)

@dataclass  
class AttitudeData:
    roll: float   # Roll angle (2 bytes when packed)
    pitch: float  # Pitch angle (2 bytes when packed)
```

### Protocol Classes
- **`Word1553B`** - Base class for all 1553B words
- **`CommandWord`** - Controls data transfer operations
- **`StatusWord`** - Reports RT status and errors
- **`DataWord`** - Carries payload data
- **`Message1553B`** - Complete message with command, data, status

### System Components
- **`BusController`** - Manages bus communication and message routing
- **`RemoteTerminal`** - Simulates RT behavior with data storage

## 📈 Performance Characteristics

### Timing
- **Word transmission**: ~20 microseconds
- **Response time**: 4-12 microseconds
- **Bus speed**: 1 MHz maximum
- **Message overhead**: 3 words (Command + Status + optional)

### Capacity
- **RT addresses**: 32 (0-31)
- **Subaddresses per RT**: 32 (0-31)
- **Data words per message**: Up to 32
- **Data throughput**: ~50 KB/s theoretical maximum

## 🧪 Test Results

```
Running MIL-STD-1553B Protocol Tests...
Ran 21 tests in 0.001s - OK

Test Coverage:
✅ Position data encoding/decoding
✅ Attitude data encoding/decoding  
✅ Command word structure
✅ Status word structure
✅ Data word parity calculation
✅ Bus Controller operations
✅ Remote Terminal operations
✅ Error handling
✅ Multi-RT scenarios
✅ Performance metrics
```

## 🎯 Specific Implementation for Your Use Case

Your requirement: **4 bytes position + 4 bytes attitude data**

### Solution:
1. **Position Data (4 bytes)**:
   - X coordinate: 2 bytes (signed int16, scaled by 100)
   - Y coordinate: 2 bytes (signed int16, scaled by 100)
   - Stored in RT subaddress 1

2. **Attitude Data (4 bytes)**:
   - Roll angle: 2 bytes (signed int16, degrees × 100)
   - Pitch angle: 2 bytes (signed int16, degrees × 100)  
   - Stored in RT subaddress 2

3. **Message Structure**:
   - Each 4-byte data block becomes 2 data words (16-bit each)
   - Total: 4 data words for both position and attitude
   - 2 separate messages (one for position, one for attitude)

### Communication Sequence:
```
Message 1: Position Data
BC → RT: Command(RT=3, SA=1, WC=2) + DataWord1(X) + DataWord2(Y)
RT → BC: Status(OK)

Message 2: Attitude Data  
BC → RT: Command(RT=3, SA=2, WC=2) + DataWord1(Roll) + DataWord2(Pitch)
RT → BC: Status(OK)
```

## 🛡️ Error Handling

- **Parity checking** on all transmitted words
- **Message error flags** in status responses
- **Range validation** for data values
- **RT address validation** before transmission
- **Timeout handling** for non-responsive terminals

## 📚 Standards Compliance

This implementation follows:
- **MIL-STD-1553B Notice 2** specification
- **20-bit word structure** (3-bit sync + 16-bit data + 1-bit parity)
- **Command/response protocol** timing requirements
- **Subaddress organization** for data management
- **Error detection and reporting** mechanisms

## 🔮 Extensibility

Easily add new data types:
```python
# Add new data type to subaddress 3
@dataclass
class VelocityData:
    vx: float
    vy: float
    vz: float
    
# Implement in BusController
def send_velocity_data(self, rt_address: int, velocity: VelocityData) -> bool:
    # Implementation follows same pattern as position/attitude
```

This implementation provides a robust, tested foundation for MIL-STD-1553B communication in avionic systems, specifically optimized for your position and attitude data requirements.
