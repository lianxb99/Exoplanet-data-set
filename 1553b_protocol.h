#ifndef MIL_STD_1553B_PROTOCOL_H
#define MIL_STD_1553B_PROTOCOL_H

#include <stdint.h>
#include <stdbool.h>

// 1553B Protocol Constants
#define MIL_STD_1553B_WORD_SIZE          16
#define MIL_STD_1553B_MAX_MESSAGE_WORDS  32
#define MIL_STD_1553B_SYNC_PATTERN       0x0000
#define MIL_STD_1553B_SYNC_PATTERN_CMD   0x0000
#define MIL_STD_1553B_SYNC_PATTERN_DATA  0x0000
#define MIL_STD_1553B_SYNC_PATTERN_STATUS 0x0000

// Message Types
typedef enum {
    MIL_STD_1553B_CMD = 0x00,
    MIL_STD_1553B_DATA = 0x01,
    MIL_STD_1553B_STATUS = 0x02
} mil_std_1553b_msg_type_t;

// Command Word Structure (16 bits)
typedef struct {
    uint16_t sync_pattern : 3;      // Always 000
    uint16_t remote_terminal : 5;   // RT address (0-31)
    uint16_t transmit_receive : 1;  // 0=receive, 1=transmit
    uint16_t subaddress : 5;        // Subaddress (0-31)
    uint16_t word_count : 5;        // Number of data words (0-31)
    uint16_t parity : 1;            // Odd parity bit
} mil_std_1553b_cmd_word_t;

// Status Word Structure (16 bits)
typedef struct {
    uint16_t sync_pattern : 3;      // Always 000
    uint16_t remote_terminal : 5;   // RT address (0-31)
    uint16_t message_error : 1;     // Message error flag
    uint16_t instrumentation : 1;   // Instrumentation bit
    uint16_t service_request : 1;   // Service request flag
    uint16_t reserved : 3;          // Reserved bits
    uint16_t broadcast_received : 1; // Broadcast received flag
    uint16_t busy : 1;              // Busy flag
    uint16_t subsystem_flag : 1;    // Subsystem flag
    uint16_t dynamic_bus_control : 1; // Dynamic bus control flag
    uint16_t terminal_flag : 1;     // Terminal flag
    uint16_t parity : 1;            // Odd parity bit
} mil_std_1553b_status_word_t;

// Data Word Structure (16 bits)
typedef struct {
    uint16_t sync_pattern : 3;      // Always 000
    uint16_t data : 12;             // 12-bit data payload
    uint16_t parity : 1;            // Odd parity bit
} mil_std_1553b_data_word_t;

// Position Data Structure (4 bytes = 2 words)
typedef struct {
    float x_position;               // X position in meters
    float y_position;               // Y position in meters
} position_data_t;

// Attitude Data Structure (4 bytes = 2 words)
typedef struct {
    float roll;                     // Roll angle in radians
    float pitch;                    // Pitch angle in radians
} attitude_data_t;

// Complete 1553B Message Structure
typedef struct {
    mil_std_1553b_cmd_word_t command_word;
    union {
        mil_std_1553b_data_word_t data_words[MIL_STD_1553B_MAX_MESSAGE_WORDS];
        struct {
            position_data_t position;
            attitude_data_t attitude;
        } payload;
    };
    mil_std_1553b_status_word_t status_word;
} mil_std_1553b_message_t;

// Protocol Configuration
typedef struct {
    uint8_t bus_controller_id;
    uint8_t remote_terminal_id;
    uint32_t bus_speed;             // Hz
    uint32_t message_timeout_ms;
} mil_std_1553b_config_t;

// Function Prototypes
uint16_t calculate_parity_1553b(uint16_t word);
bool validate_message_1553b(const mil_std_1553b_message_t* message);
void pack_position_data(const position_data_t* pos, mil_std_1553b_data_word_t* words);
void pack_attitude_data(const attitude_data_t* att, mil_std_1553b_data_word_t* words);
void unpack_position_data(const mil_std_1553b_data_word_t* words, position_data_t* pos);
void unpack_attitude_data(const mil_std_1553b_data_word_t* words, attitude_data_t* att);

#endif // MIL_STD_1553B_PROTOCOL_H