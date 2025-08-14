#ifndef MIL_STD_1553B_BUS_CONTROLLER_H
#define MIL_STD_1553B_BUS_CONTROLLER_H

#include "1553b_protocol.h"
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>

// Bus Controller State
typedef enum {
    BC_STATE_IDLE,
    BC_STATE_TRANSMITTING,
    BC_STATE_WAITING_RESPONSE,
    BC_STATE_ERROR
} bc_state_t;

// Bus Controller Structure
typedef struct {
    uint8_t controller_id;
    bc_state_t state;
    mil_std_1553b_config_t config;
    
    // Message queues
    struct message_queue_entry {
        mil_std_1553b_message_t message;
        uint32_t timestamp;
        bool processed;
    }* transmit_queue;
    int queue_size;
    int queue_head;
    int queue_tail;
    
    // Statistics
    uint32_t messages_sent;
    uint32_t messages_received;
    uint32_t errors;
    
    // Threading
    pthread_t controller_thread;
    pthread_mutex_t queue_mutex;
    pthread_cond_t queue_condition;
    bool running;
} bus_controller_t;

// Function Prototypes
bus_controller_t* bc_init(uint8_t controller_id, const mil_std_1553b_config_t* config);
void bc_cleanup(bus_controller_t* bc);
bool bc_start(bus_controller_t* bc);
void bc_stop(bus_controller_t* bc);
bool bc_queue_message(bus_controller_t* bc, const mil_std_1553b_message_t* message);
void bc_get_statistics(bus_controller_t* bc, uint32_t* sent, uint32_t* received, uint32_t* errors);
bool bc_send_position_attitude(bus_controller_t* bc, uint8_t rt_address, uint8_t subaddress, 
                              const position_data_t* position, const attitude_data_t* attitude);
void print_1553b_message(const mil_std_1553b_message_t* message);

#endif // MIL_STD_1553B_BUS_CONTROLLER_H