# MIL-STD-1553B Communication Protocol Implementation Guide

## Overview

This document provides a complete implementation of the MIL-STD-1553B communication protocol, specifically designed to handle 4 bytes of position data and 4 bytes of attitude data between avionic systems.

## Protocol Basics

MIL-STD-1553B is a military standard that defines:
- **Time-division multiplexed data bus**
- **Command/response protocol**
- **Bus Controller (BC)** manages all communications
- **Remote Terminals (RTs)** respond to BC commands
- **16-bit data words** for information transfer

## Data Word Structure

Each 1553B word consists of 20 bits:
```
| Sync (3 bits) | Data (16 bits) | Parity (1 bit) |
```

### Word Types:
1. **Command Word**: Controls data transfer operations
2. **Data Word**: Carries actual payload data
3. **Status Word**: Reports RT status and errors

## Data Organization

### Position Data (4 bytes)
- **X coordinate**: 2 bytes (scaled float to int16)
- **Y coordinate**: 2 bytes (scaled float to int16)
- **Storage**: Subaddress 1, 2 data words

### Attitude Data (4 bytes)
- **Roll angle**: 2 bytes (degrees * 100)
- **Pitch angle**: 2 bytes (degrees * 100)
- **Storage**: Subaddress 2, 2 data words

## Communication Flow

### 1. BC to RT Data Transfer (Position Data)

```
Step 1: BC sends Command Word
┌─────────────────────────────────────────────────────────┐
│ RT Addr │ T/R │ Subaddr │ Word Count │ Sync │ Parity   │
│   (5)   │ (1) │   (5)   │    (5)     │ (3)  │   (1)    │
│    3    │  0  │    1    │     2      │ 100  │    X     │
└─────────────────────────────────────────────────────────┘

Step 2: BC sends Data Words
Data Word 1: Position X (scaled to int16)
Data Word 2: Position Y (scaled to int16)

Step 3: RT responds with Status Word
┌─────────────────────────────────────────────────────────┐
│ RT Addr │ Flags (10 bits)              │ Sync │ Parity │
│   (5)   │ ME│IN│SR│3│BC│BU│SS│DB│TF│   │ (3)  │   (1)  │
│    3    │ 0 │0 │0 │0│0 │0 │0 │0 │0 │   │ 100  │    X   │
└─────────────────────────────────────────────────────────┘
```

### 2. RT to BC Data Transfer (Request Data)

```
Step 1: BC sends Command Word (T/R bit = 1)
┌─────────────────────────────────────────────────────────┐
│ RT Addr │ T/R │ Subaddr │ Word Count │ Sync │ Parity   │
│   (5)   │ (1) │   (5)   │    (5)     │ (3)  │   (1)    │
│    3    │  1  │    1    │     2      │ 100  │    X     │
└─────────────────────────────────────────────────────────┘

Step 2: RT responds with Status Word + Data Words
Status Word: RT status information
Data Word 1: Position X (from subaddress 1)
Data Word 2: Position Y (from subaddress 1)
```

## Implementation Details

### Key Classes

1. **PositionData**: Handles X,Y coordinate data
2. **AttitudeData**: Handles roll,pitch angle data
3. **CommandWord**: Creates proper 1553B command words
4. **StatusWord**: Manages RT status reporting
5. **DataWord**: Encapsulates payload data
6. **BusController**: Manages all bus communications
7. **RemoteTerminal**: Simulates RT behavior

### Message Format Example

For sending position data X=123.45, Y=678.90:

1. **Scale data**: X=12345, Y=67890 (multiply by 100)
2. **Pack to words**: 
   - Word 1: 0x3039 (12345 in hex)
   - Word 2: 0x109B2 → 0x09B2 (67890 & 0xFFFF)
3. **Create command**: RT=3, T/R=0, SA=1, WC=2
4. **Send sequence**: Command → Data1 → Data2 → Status

### Error Handling

The protocol includes comprehensive error handling:
- **Parity checking** on all words
- **Message error flags** in status words
- **Timeout detection** for non-responsive RTs
- **Data validation** during pack/unpack operations

## Usage Example

```python
# Create system components
bc = BusController()
rt = RemoteTerminal(address=3)
bc.add_remote_terminal(rt)

# Create data
position = PositionData(x=123.45, y=678.90)
attitude = AttitudeData(roll=15.5, pitch=-10.25)

# Send data (BC → RT)
bc.send_position_data(3, position)
bc.send_attitude_data(3, attitude)

# Request data (RT → BC)
received_pos = bc.request_position_data(3)
received_att = bc.request_attitude_data(3)
```

## Subaddress Mapping

| Subaddress | Data Type | Word Count | Description |
|------------|-----------|------------|-------------|
| 1          | Position  | 2          | X,Y coordinates |
| 2          | Attitude  | 2          | Roll,Pitch angles |
| 3-30       | Available | Variable   | Custom data types |
| 31         | Mode Code | 0 or 1     | Special commands |

## Timing Characteristics

- **Word transmission time**: ~20 microseconds
- **Response time**: 4-12 microseconds after command
- **Bus access**: Round-robin or priority-based
- **Maximum bus speed**: 1 MHz

## Benefits of This Implementation

1. **Standards Compliant**: Follows MIL-STD-1553B specification
2. **Deterministic**: Predictable timing and behavior
3. **Reliable**: Built-in error detection and status reporting
4. **Scalable**: Easy to add more data types and RTs
5. **Maintainable**: Clear separation of concerns and well-documented

## Testing and Validation

The implementation includes:
- **Unit tests** for each component
- **Integration tests** for complete message flows
- **Error injection** for robustness testing
- **Performance benchmarks** for timing validation

This implementation provides a solid foundation for avionic systems requiring reliable, deterministic communication of position and attitude data.