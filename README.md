# 1553B Communication Protocol Implementation

This project provides a complete implementation of the MIL-STD-1553B communication protocol for transmitting position and attitude data between a Bus Controller (BC) and Remote Terminals (RT).

## Overview

The MIL-STD-1553B is a military standard for digital time division command/response multiplex data bus. This implementation demonstrates how to:

- Pack 4 bytes of position data (X, Y coordinates)
- Pack 4 bytes of attitude data (roll, pitch angles)
- Transmit data using the 1553B protocol
- Handle message validation and error checking
- Manage communication between multiple terminals

## Protocol Structure

### Message Format
Each 1553B message consists of three parts:
1. **Command Word** (16 bits) - Contains addressing and control information
2. **Data Words** (16 bits each) - Contains the actual payload data
3. **Status Word** (16 bits) - Contains response and status information

### Data Packing
- **Position Data**: 2 words (4 bytes total)
  - Word 0: X position (12-bit fixed-point, range: ±1000m)
  - Word 1: Y position (12-bit fixed-point, range: ±1000m)
- **Attitude Data**: 2 words (4 bytes total)
  - Word 2: Roll angle (12-bit fixed-point, range: 0-2π radians)
  - Word 3: Pitch angle (12-bit fixed-point, range: 0-2π radians)

## Communication Process

### 1. Message Creation
```c
// Create position and attitude data
position_data_t position = {100.5f, 200.3f};  // X=100.5m, Y=200.3m
attitude_data_t attitude = {0.1f, 0.05f};     // Roll=0.1rad, Pitch=0.05rad

// Create 1553B message
mil_std_1553b_message_t message;
create_1553b_message(&message, rt_address, subaddress, &position, &attitude);
```

### 2. Data Packing
The protocol automatically:
- Converts float values to 12-bit fixed-point representation
- Adds sync patterns and parity bits
- Validates message structure

### 3. Message Transmission
```c
// Bus Controller sends message
bc_send_position_attitude(bc, rt_address, subaddress, &position, &attitude);
```

### 4. Message Reception
```c
// Remote Terminal receives and processes message
bool success = extract_1553b_data(&message, &received_position, &received_attitude);
```

## File Structure

- `1553b_protocol.h` - Protocol definitions and data structures
- `1553b_protocol.c` - Core protocol implementation (packing/unpacking)
- `1553b_bus_controller.c` - Bus Controller implementation
- `1553b_remote_terminal.c` - Remote Terminal implementation
- `example_1553b_system.c` - Complete working example
- `Makefile` - Build configuration

## Building and Running

### Prerequisites
```bash
# Install build tools (Ubuntu/Debian)
sudo apt-get install build-essential
```

### Compile
```bash
make
```

### Run Example
```bash
make run
```

### Debug Build
```bash
make debug
```

### Clean Build
```bash
make clean
```

## Usage Example

```c
#include "1553b_protocol.h"

int main() {
    // Configure 1553B system
    mil_std_1553b_config_t config = {
        .bus_controller_id = 1,
        .remote_terminal_id = 2,
        .bus_speed = 1000000, // 1 MHz
        .message_timeout_ms = 100
    };
    
    // Initialize components
    bus_controller_t* bc = bc_init(config.bus_controller_id, &config);
    remote_terminal_t* rt = rt_init(config.remote_terminal_id, &config);
    
    // Start communication
    bc_start(bc);
    rt_start(rt);
    
    // Send position and attitude data
    position_data_t position = {100.0f, 200.0f};
    attitude_data_t attitude = {0.1f, 0.05f};
    
    bc_send_position_attitude(bc, 2, 1, &position, &attitude);
    
    // Cleanup
    bc_stop(bc);
    rt_stop(rt);
    bc_cleanup(bc);
    rt_cleanup(rt);
    
    return 0;
}
```

## Protocol Features

### Error Detection
- **Parity Checking**: Odd parity on all words
- **Message Validation**: Sync pattern and field range validation
- **Timeout Handling**: Configurable message timeouts

### Thread Safety
- Multi-threaded message processing
- Thread-safe data access with mutexes
- Asynchronous message queuing

### Performance
- Efficient fixed-point data packing
- Minimal memory allocation
- Configurable bus speeds

## Data Format Details

### Position Data Encoding
- **Range**: ±1000 meters
- **Resolution**: ~0.5 meters (12-bit precision)
- **Format**: Fixed-point with sign bit

### Attitude Data Encoding
- **Range**: 0 to 2π radians
- **Resolution**: ~0.0015 radians (12-bit precision)
- **Format**: Unsigned fixed-point

### Message Timing
- **Command Word**: 16 μs at 1 MHz
- **Data Words**: 16 μs each
- **Status Word**: 16 μs
- **Total Message**: ~80 μs for 4 data words

## Subaddress Usage

- **Subaddress 1**: Position and attitude data request (T/R=1)
- **Subaddress 2**: Position and attitude data update (T/R=0)

## Error Handling

The implementation includes comprehensive error handling:
- Invalid message structure detection
- Parity error detection
- Timeout handling
- Queue overflow protection
- Thread synchronization errors

## Testing

Run the example to see the protocol in action:
```bash
make run
```

The example will:
1. Generate simulated position and attitude data
2. Send data requests and updates
3. Display communication statistics
4. Show real-time terminal status

## License

This implementation is provided as an educational example of the 1553B protocol. It is not intended for production use without proper validation and testing.
