#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE
#include "1553b_protocol.h"
#include "1553b_bus_controller.h"
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

// Message Queue Entry
typedef struct message_queue_entry message_queue_entry_t;

// Initialize bus controller
bus_controller_t* bc_init(uint8_t controller_id, const mil_std_1553b_config_t* config) {
    bus_controller_t* bc = malloc(sizeof(bus_controller_t));
    if (!bc) {
        return NULL;
    }
    
    bc->controller_id = controller_id;
    bc->state = BC_STATE_IDLE;
    bc->config = *config;
    
    // Initialize message queue
    bc->queue_size = 100;
    bc->transmit_queue = malloc(bc->queue_size * sizeof(message_queue_entry_t));
    bc->queue_head = 0;
    bc->queue_tail = 0;
    
    // Initialize statistics
    bc->messages_sent = 0;
    bc->messages_received = 0;
    bc->errors = 0;
    
    // Initialize threading
    pthread_mutex_init(&bc->queue_mutex, NULL);
    pthread_cond_init(&bc->queue_condition, NULL);
    bc->running = false;
    
    return bc;
}

// Cleanup bus controller
void bc_cleanup(bus_controller_t* bc) {
    if (!bc) {
        return;
    }
    
    bc->running = false;
    pthread_join(bc->controller_thread, NULL);
    
    pthread_mutex_destroy(&bc->queue_mutex);
    pthread_cond_destroy(&bc->queue_condition);
    
    free(bc->transmit_queue);
    free(bc);
}

// Add message to transmit queue
bool bc_queue_message(bus_controller_t* bc, const mil_std_1553b_message_t* message) {
    if (!bc || !message) {
        return false;
    }
    
    pthread_mutex_lock(&bc->queue_mutex);
    
    // Check if queue is full
    int next_tail = (bc->queue_tail + 1) % bc->queue_size;
    if (next_tail == bc->queue_head) {
        pthread_mutex_unlock(&bc->queue_mutex);
        return false; // Queue full
    }
    
    // Add message to queue
    bc->transmit_queue[bc->queue_tail].message = *message;
    bc->transmit_queue[bc->queue_tail].timestamp = (uint32_t)time(NULL);
    bc->transmit_queue[bc->queue_tail].processed = false;
    bc->queue_tail = next_tail;
    
    pthread_cond_signal(&bc->queue_condition);
    pthread_mutex_unlock(&bc->queue_mutex);
    
    return true;
}

// Simulate 1553B bus transmission
static bool transmit_message_1553b(bus_controller_t* bc, const mil_std_1553b_message_t* message) {
    if (!bc || !message) {
        return false;
    }
    
    // Validate message before transmission
    if (!validate_message_1553b(message)) {
        bc->errors++;
        return false;
    }
    
    // Simulate transmission delay (microseconds)
    usleep(1000); // 1ms delay
    
    // Simulate transmission success (90% success rate)
    if (rand() % 100 < 90) {
        bc->messages_sent++;
        return true;
    } else {
        bc->errors++;
        return false;
    }
}

// Bus controller main thread function
static void* bc_controller_thread(void* arg) {
    bus_controller_t* bc = (bus_controller_t*)arg;
    
    while (bc->running) {
        pthread_mutex_lock(&bc->queue_mutex);
        
        // Wait for messages in queue
        while (bc->queue_head == bc->queue_tail && bc->running) {
            pthread_cond_wait(&bc->queue_condition, &bc->queue_mutex);
        }
        
        if (!bc->running) {
            pthread_mutex_unlock(&bc->queue_mutex);
            break;
        }
        
        // Process message from queue
        message_queue_entry_t* entry = &bc->transmit_queue[bc->queue_head];
        bc->queue_head = (bc->queue_head + 1) % bc->queue_size;
        
        pthread_mutex_unlock(&bc->queue_mutex);
        
        // Transmit message
        bc->state = BC_STATE_TRANSMITTING;
        bool success = transmit_message_1553b(bc, &entry->message);
        
        if (success) {
            bc->state = BC_STATE_WAITING_RESPONSE;
            // Simulate response wait time
            usleep(500); // 0.5ms
            bc->messages_received++;
        } else {
            bc->state = BC_STATE_ERROR;
        }
        
        entry->processed = true;
        bc->state = BC_STATE_IDLE;
    }
    
    return NULL;
}

// Start bus controller
bool bc_start(bus_controller_t* bc) {
    if (!bc) {
        return false;
    }
    
    bc->running = true;
    if (pthread_create(&bc->controller_thread, NULL, bc_controller_thread, bc) != 0) {
        bc->running = false;
        return false;
    }
    
    return true;
}

// Stop bus controller
void bc_stop(bus_controller_t* bc) {
    if (!bc) {
        return;
    }
    
    bc->running = false;
    pthread_cond_signal(&bc->queue_condition);
}

// Get bus controller statistics
void bc_get_statistics(bus_controller_t* bc, uint32_t* sent, uint32_t* received, uint32_t* errors) {
    if (!bc) {
        return;
    }
    
    pthread_mutex_lock(&bc->queue_mutex);
    if (sent) *sent = bc->messages_sent;
    if (received) *received = bc->messages_received;
    if (errors) *errors = bc->errors;
    pthread_mutex_unlock(&bc->queue_mutex);
}

// Send position and attitude data
bool bc_send_position_attitude(bus_controller_t* bc, 
                              uint8_t rt_address,
                              uint8_t subaddress,
                              const position_data_t* position,
                              const attitude_data_t* attitude) {
    if (!bc || !position || !attitude) {
        return false;
    }
    
    mil_std_1553b_message_t message;
    create_1553b_message(&message, rt_address, subaddress, position, attitude);
    
    return bc_queue_message(bc, &message);
}

// Print message details for debugging
void print_1553b_message(const mil_std_1553b_message_t* message) {
    if (!message) {
        return;
    }
    
    printf("1553B Message:\n");
    printf("  Command Word: RT=%d, T/R=%d, SA=%d, WC=%d\n",
           message->command_word.remote_terminal,
           message->command_word.transmit_receive,
           message->command_word.subaddress,
           message->command_word.word_count);
    
    printf("  Data Words: ");
    for (int i = 0; i < message->command_word.word_count; i++) {
        union {
            mil_std_1553b_data_word_t data_word;
            uint16_t raw;
        } data_union;
        data_union.data_word = message->data_words[i];
        printf("0x%04X ", data_union.raw);
    }
    printf("\n");
    
    printf("  Status Word: RT=%d, ME=%d, SR=%d, BF=%d\n",
           message->status_word.remote_terminal,
           message->status_word.message_error,
           message->status_word.service_request,
           message->status_word.busy);
}