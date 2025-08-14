#include "1553b_protocol.h"
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Calculate odd parity for 1553B words
uint16_t calculate_parity_1553b(uint16_t word) {
    uint16_t parity = 0;
    uint16_t temp = word & 0x7FFF; // Exclude parity bit
    
    // Count number of 1s
    while (temp) {
        parity ^= (temp & 1);
        temp >>= 1;
    }
    
    return parity;
}

// Validate 1553B message structure and parity
bool validate_message_1553b(const mil_std_1553b_message_t* message) {
    if (!message) {
        return false;
    }
    
    // Validate command word
    if (message->command_word.sync_pattern != 0) {
        return false;
    }
    
    if (message->command_word.remote_terminal > 31) {
        return false;
    }
    
    if (message->command_word.subaddress > 31) {
        return false;
    }
    
    if (message->command_word.word_count > 31) {
        return false;
    }
    
    // Check command word parity
    union {
        mil_std_1553b_cmd_word_t cmd;
        uint16_t raw;
    } cmd_union;
    cmd_union.cmd = message->command_word;
    uint16_t expected_parity = calculate_parity_1553b(cmd_union.raw & 0x7FFF);
    if (message->command_word.parity != expected_parity) {
        return false;
    }
    
    // Validate status word
    if (message->status_word.sync_pattern != 0) {
        return false;
    }
    
    if (message->status_word.remote_terminal > 31) {
        return false;
    }
    
    // Check status word parity
    union {
        mil_std_1553b_status_word_t status;
        uint16_t raw;
    } status_union;
    status_union.status = message->status_word;
    expected_parity = calculate_parity_1553b(status_union.raw & 0x7FFF);
    if (message->status_word.parity != expected_parity) {
        return false;
    }
    
    return true;
}

// Pack position data into 1553B data words
void pack_position_data(const position_data_t* pos, mil_std_1553b_data_word_t* words) {
    if (!pos || !words) {
        return;
    }
    
    // Convert float to fixed-point representation (12-bit resolution)
    // Scale position to fit in 12-bit range (-2048 to 2047)
    const float max_position = 2047.0f;
    const float scale_factor = max_position / 1000.0f; // 1000m range
    
    int16_t x_scaled = (int16_t)(pos->x_position * scale_factor);
    int16_t y_scaled = (int16_t)(pos->y_position * scale_factor);
    
    // Clamp values to 12-bit range
    x_scaled = (x_scaled > 2047) ? 2047 : (x_scaled < -2048) ? -2048 : x_scaled;
    y_scaled = (y_scaled > 2047) ? 2047 : (y_scaled < -2048) ? -2048 : y_scaled;
    
    // Pack into data words
    words[0].sync_pattern = 0;
    words[0].data = (uint16_t)(x_scaled & 0x0FFF);
    union {
        mil_std_1553b_data_word_t data_word;
        uint16_t raw;
    } data_union0;
    data_union0.data_word = words[0];
    words[0].parity = calculate_parity_1553b(data_union0.raw & 0x7FFF);
    
    words[1].sync_pattern = 0;
    words[1].data = (uint16_t)(y_scaled & 0x0FFF);
    union {
        mil_std_1553b_data_word_t data_word;
        uint16_t raw;
    } data_union1;
    data_union1.data_word = words[1];
    words[1].parity = calculate_parity_1553b(data_union1.raw & 0x7FFF);
}

// Pack attitude data into 1553B data words
void pack_attitude_data(const attitude_data_t* att, mil_std_1553b_data_word_t* words) {
    if (!att || !words) {
        return;
    }
    
    // Convert radians to fixed-point representation
    // Scale angles to fit in 12-bit range (0 to 4095 for 0 to 2π)
    const float max_angle = 2.0f * M_PI;
    const float scale_factor = 4095.0f / max_angle;
    
    uint16_t roll_scaled = (uint16_t)(fmod(att->roll + max_angle, max_angle) * scale_factor);
    uint16_t pitch_scaled = (uint16_t)(fmod(att->pitch + max_angle, max_angle) * scale_factor);
    
    // Pack into data words
    words[0].sync_pattern = 0;
    words[0].data = roll_scaled & 0x0FFF;
    union {
        mil_std_1553b_data_word_t data_word;
        uint16_t raw;
    } data_union0;
    data_union0.data_word = words[0];
    words[0].parity = calculate_parity_1553b(data_union0.raw & 0x7FFF);
    
    words[1].sync_pattern = 0;
    words[1].data = pitch_scaled & 0x0FFF;
    union {
        mil_std_1553b_data_word_t data_word;
        uint16_t raw;
    } data_union1;
    data_union1.data_word = words[1];
    words[1].parity = calculate_parity_1553b(data_union1.raw & 0x7FFF);
}

// Unpack position data from 1553B data words
void unpack_position_data(const mil_std_1553b_data_word_t* words, position_data_t* pos) {
    if (!words || !pos) {
        return;
    }
    
    // Extract scaled values
    int16_t x_scaled = (int16_t)(words[0].data & 0x0FFF);
    int16_t y_scaled = (int16_t)(words[1].data & 0x0FFF);
    
    // Handle sign extension for negative values
    if (x_scaled & 0x0800) {
        x_scaled |= 0xF000; // Sign extend
    }
    if (y_scaled & 0x0800) {
        y_scaled |= 0xF000; // Sign extend
    }
    
    // Convert back to float
    const float max_position = 2047.0f;
    const float scale_factor = 1000.0f / max_position;
    
    pos->x_position = (float)x_scaled * scale_factor;
    pos->y_position = (float)y_scaled * scale_factor;
}

// Unpack attitude data from 1553B data words
void unpack_attitude_data(const mil_std_1553b_data_word_t* words, attitude_data_t* att) {
    if (!words || !att) {
        return;
    }
    
    // Extract scaled values
    uint16_t roll_scaled = words[0].data & 0x0FFF;
    uint16_t pitch_scaled = words[1].data & 0x0FFF;
    
    // Convert back to radians
    const float max_angle = 2.0f * M_PI;
    const float scale_factor = max_angle / 4095.0f;
    
    att->roll = (float)roll_scaled * scale_factor;
    att->pitch = (float)pitch_scaled * scale_factor;
}

// Create a complete 1553B message with position and attitude data
void create_1553b_message(mil_std_1553b_message_t* message, 
                         uint8_t rt_address,
                         uint8_t subaddress,
                         const position_data_t* position,
                         const attitude_data_t* attitude) {
    if (!message || !position || !attitude) {
        return;
    }
    
    // Initialize command word
    message->command_word.sync_pattern = 0;
    message->command_word.remote_terminal = rt_address;
    message->command_word.transmit_receive = 1; // Transmit
    message->command_word.subaddress = subaddress;
    message->command_word.word_count = 4; // 4 data words (2 for position + 2 for attitude)
    union {
        mil_std_1553b_cmd_word_t cmd;
        uint16_t raw;
    } cmd_union;
    cmd_union.cmd = message->command_word;
    message->command_word.parity = calculate_parity_1553b(cmd_union.raw & 0x7FFF);
    
    // Pack position data (words 0-1)
    pack_position_data(position, &message->data_words[0]);
    
    // Pack attitude data (words 2-3)
    pack_attitude_data(attitude, &message->data_words[2]);
    
    // Initialize status word
    message->status_word.sync_pattern = 0;
    message->status_word.remote_terminal = rt_address;
    message->status_word.message_error = 0;
    message->status_word.instrumentation = 0;
    message->status_word.service_request = 0;
    message->status_word.reserved = 0;
    message->status_word.broadcast_received = 0;
    message->status_word.busy = 0;
    message->status_word.subsystem_flag = 0;
    message->status_word.dynamic_bus_control = 0;
    message->status_word.terminal_flag = 0;
    union {
        mil_std_1553b_status_word_t status;
        uint16_t raw;
    } status_union;
    status_union.status = message->status_word;
    message->status_word.parity = calculate_parity_1553b(status_union.raw & 0x7FFF);
}

// Extract position and attitude data from a 1553B message
bool extract_1553b_data(const mil_std_1553b_message_t* message,
                       position_data_t* position,
                       attitude_data_t* attitude) {
    if (!message || !position || !attitude) {
        return false;
    }
    
    // Validate message
    if (!validate_message_1553b(message)) {
        return false;
    }
    
    // Check word count
    if (message->command_word.word_count != 4) {
        return false;
    }
    
    // Unpack position data (words 0-1)
    unpack_position_data(&message->data_words[0], position);
    
    // Unpack attitude data (words 2-3)
    unpack_attitude_data(&message->data_words[2], attitude);
    
    return true;
}