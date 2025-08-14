#ifndef MIL_STD_1553B_REMOTE_TERMINAL_H
#define MIL_STD_1553B_REMOTE_TERMINAL_H

#include "1553b_protocol.h"
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>

// Remote Terminal State
typedef enum {
    RT_STATE_IDLE,
    RT_STATE_RECEIVING,
    RT_STATE_PROCESSING,
    RT_STATE_TRANSMITTING,
    RT_STATE_ERROR
} rt_state_t;

// Remote Terminal Structure
typedef struct {
    uint8_t terminal_id;
    rt_state_t state;
    mil_std_1553b_config_t config;
    
    // Data storage
    position_data_t current_position;
    attitude_data_t current_attitude;
    
    // Message processing
    mil_std_1553b_message_t last_received_message;
    mil_std_1553b_message_t response_message;
    bool message_pending;
    
    // Statistics
    uint32_t messages_received;
    uint32_t messages_transmitted;
    uint32_t errors;
    
    // Threading
    pthread_t terminal_thread;
    pthread_mutex_t data_mutex;
    pthread_cond_t message_condition;
    bool running;
} remote_terminal_t;

// Function Prototypes
remote_terminal_t* rt_init(uint8_t terminal_id, const mil_std_1553b_config_t* config);
void rt_cleanup(remote_terminal_t* rt);
bool rt_start(remote_terminal_t* rt);
void rt_stop(remote_terminal_t* rt);
void rt_update_position(remote_terminal_t* rt, const position_data_t* position);
void rt_update_attitude(remote_terminal_t* rt, const attitude_data_t* attitude);
void rt_get_statistics(remote_terminal_t* rt, uint32_t* received, uint32_t* transmitted, uint32_t* errors);
void rt_get_position(remote_terminal_t* rt, position_data_t* position);
void rt_get_attitude(remote_terminal_t* rt, attitude_data_t* attitude);
void print_rt_status(remote_terminal_t* rt);

#endif // MIL_STD_1553B_REMOTE_TERMINAL_H