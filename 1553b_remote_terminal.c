#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE
#include "1553b_protocol.h"
#include "1553b_remote_terminal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>

// Function declarations
void create_1553b_message(mil_std_1553b_message_t* message, 
                         uint8_t rt_address,
                         uint8_t subaddress,
                         const position_data_t* position,
                         const attitude_data_t* attitude);
bool extract_1553b_data(const mil_std_1553b_message_t* message,
                       position_data_t* position,
                       attitude_data_t* attitude);


// Initialize remote terminal
remote_terminal_t* rt_init(uint8_t terminal_id, const mil_std_1553b_config_t* config) {
    remote_terminal_t* rt = malloc(sizeof(remote_terminal_t));
    if (!rt) {
        return NULL;
    }
    
    rt->terminal_id = terminal_id;
    rt->state = RT_STATE_IDLE;
    rt->config = *config;
    
    // Initialize data
    rt->current_position.x_position = 0.0f;
    rt->current_position.y_position = 0.0f;
    rt->current_attitude.roll = 0.0f;
    rt->current_attitude.pitch = 0.0f;
    
    // Initialize message processing
    memset(&rt->last_received_message, 0, sizeof(mil_std_1553b_message_t));
    memset(&rt->response_message, 0, sizeof(mil_std_1553b_message_t));
    rt->message_pending = false;
    
    // Initialize statistics
    rt->messages_received = 0;
    rt->messages_transmitted = 0;
    rt->errors = 0;
    
    // Initialize threading
    pthread_mutex_init(&rt->data_mutex, NULL);
    pthread_cond_init(&rt->message_condition, NULL);
    rt->running = false;
    
    return rt;
}

// Cleanup remote terminal
void rt_cleanup(remote_terminal_t* rt) {
    if (!rt) {
        return;
    }
    
    rt->running = false;
    pthread_join(rt->terminal_thread, NULL);
    
    pthread_mutex_destroy(&rt->data_mutex);
    pthread_cond_destroy(&rt->message_condition);
    
    free(rt);
}

// Update position data
void rt_update_position(remote_terminal_t* rt, const position_data_t* position) {
    if (!rt || !position) {
        return;
    }
    
    pthread_mutex_lock(&rt->data_mutex);
    rt->current_position = *position;
    pthread_mutex_unlock(&rt->data_mutex);
}

// Update attitude data
void rt_update_attitude(remote_terminal_t* rt, const attitude_data_t* attitude) {
    if (!rt || !attitude) {
        return;
    }
    
    pthread_mutex_lock(&rt->data_mutex);
    rt->current_attitude = *attitude;
    pthread_mutex_unlock(&rt->data_mutex);
}

// Process received message
static bool process_received_message(remote_terminal_t* rt, const mil_std_1553b_message_t* message) {
    if (!rt || !message) {
        return false;
    }
    
    // Validate message
    if (!validate_message_1553b(message)) {
        rt->errors++;
        return false;
    }
    
    // Check if message is for this terminal
    if (message->command_word.remote_terminal != rt->terminal_id) {
        return false; // Not for this terminal
    }
    
    rt->messages_received++;
    
    // Process based on subaddress
    switch (message->command_word.subaddress) {
        case 1: // Position and attitude data request
            if (message->command_word.transmit_receive == 1) { // Transmit request
                // Prepare response with current position and attitude
                pthread_mutex_lock(&rt->data_mutex);
                create_1553b_message(&rt->response_message, 
                                   rt->terminal_id, 
                                   message->command_word.subaddress,
                                   &rt->current_position,
                                   &rt->current_attitude);
                pthread_mutex_unlock(&rt->data_mutex);
                
                rt->message_pending = true;
                return true;
            }
            break;
            
        case 2: // Position data update
            if (message->command_word.transmit_receive == 0) { // Receive
                position_data_t new_position;
                attitude_data_t new_attitude;
                
                if (extract_1553b_data(message, &new_position, &new_attitude)) {
                    rt_update_position(rt, &new_position);
                    rt_update_attitude(rt, &new_attitude);
                    return true;
                }
            }
            break;
            
        default:
            rt->errors++;
            return false;
    }
    
    return false;
}

// Simulate message reception
static bool receive_message_1553b(remote_terminal_t* rt, mil_std_1553b_message_t* message) {
    if (!rt || !message) {
        return false;
    }
    
    // Simulate reception delay
    usleep(500); // 0.5ms delay
    
    // Simulate reception success (95% success rate)
    if (rand() % 100 < 95) {
        return true;
    } else {
        rt->errors++;
        return false;
    }
}

// Remote terminal main thread function
static void* rt_terminal_thread(void* arg) {
    remote_terminal_t* rt = (remote_terminal_t*)arg;
    
    while (rt->running) {
        // Simulate message reception
        mil_std_1553b_message_t received_message;
        
        rt->state = RT_STATE_RECEIVING;
        if (receive_message_1553b(rt, &received_message)) {
            rt->state = RT_STATE_PROCESSING;
            
            // Process the received message
            if (process_received_message(rt, &received_message)) {
                rt->last_received_message = received_message;
                
                // If response is pending, transmit it
                if (rt->message_pending) {
                    rt->state = RT_STATE_TRANSMITTING;
                    
                    // Simulate transmission delay
                    usleep(1000); // 1ms
                    
                    rt->messages_transmitted++;
                    rt->message_pending = false;
                }
            }
        } else {
            rt->state = RT_STATE_ERROR;
        }
        
        rt->state = RT_STATE_IDLE;
        
        // Small delay between message cycles
        usleep(100); // 0.1ms
    }
    
    return NULL;
}

// Start remote terminal
bool rt_start(remote_terminal_t* rt) {
    if (!rt) {
        return false;
    }
    
    rt->running = true;
    if (pthread_create(&rt->terminal_thread, NULL, rt_terminal_thread, rt) != 0) {
        rt->running = false;
        return false;
    }
    
    return true;
}

// Stop remote terminal
void rt_stop(remote_terminal_t* rt) {
    if (!rt) {
        return;
    }
    
    rt->running = false;
}

// Get remote terminal statistics
void rt_get_statistics(remote_terminal_t* rt, uint32_t* received, uint32_t* transmitted, uint32_t* errors) {
    if (!rt) {
        return;
    }
    
    pthread_mutex_lock(&rt->data_mutex);
    if (received) *received = rt->messages_received;
    if (transmitted) *transmitted = rt->messages_transmitted;
    if (errors) *errors = rt->errors;
    pthread_mutex_unlock(&rt->data_mutex);
}

// Get current position data
void rt_get_position(remote_terminal_t* rt, position_data_t* position) {
    if (!rt || !position) {
        return;
    }
    
    pthread_mutex_lock(&rt->data_mutex);
    *position = rt->current_position;
    pthread_mutex_unlock(&rt->data_mutex);
}

// Get current attitude data
void rt_get_attitude(remote_terminal_t* rt, attitude_data_t* attitude) {
    if (!rt || !attitude) {
        return;
    }
    
    pthread_mutex_lock(&rt->data_mutex);
    *attitude = rt->current_attitude;
    pthread_mutex_unlock(&rt->data_mutex);
}

// Print remote terminal status
void print_rt_status(remote_terminal_t* rt) {
    if (!rt) {
        return;
    }
    
    position_data_t pos;
    attitude_data_t att;
    
    rt_get_position(rt, &pos);
    rt_get_attitude(rt, &att);
    
    printf("Remote Terminal %d Status:\n", rt->terminal_id);
    printf("  State: %d\n", rt->state);
    printf("  Position: X=%.2f m, Y=%.2f m\n", pos.x_position, pos.y_position);
    printf("  Attitude: Roll=%.4f rad, Pitch=%.4f rad\n", att.roll, att.pitch);
    printf("  Messages: Received=%d, Transmitted=%d, Errors=%d\n",
           rt->messages_received, rt->messages_transmitted, rt->errors);
}