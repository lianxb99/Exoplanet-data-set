#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE
#include "1553b_protocol.h"
#include "1553b_bus_controller.h"
#include "1553b_remote_terminal.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>

// Generate simulated position data
void generate_position_data(position_data_t* position, float time) {
    position->x_position = 100.0f * sin(time * 0.1f); // Oscillating X position
    position->y_position = 50.0f * cos(time * 0.15f);  // Oscillating Y position
}

// Generate simulated attitude data
void generate_attitude_data(attitude_data_t* attitude, float time) {
    attitude->roll = 0.1f * sin(time * 0.2f);   // Small roll oscillations
    attitude->pitch = 0.05f * cos(time * 0.25f); // Small pitch oscillations
}

// Print system statistics
void print_system_statistics(bus_controller_t* bc, remote_terminal_t* rt) {
    uint32_t bc_sent, bc_received, bc_errors;
    uint32_t rt_received, rt_transmitted, rt_errors;
    
    bc_get_statistics(bc, &bc_sent, &bc_received, &bc_errors);
    rt_get_statistics(rt, &rt_received, &rt_transmitted, &rt_errors);
    
    printf("\n=== 1553B System Statistics ===\n");
    printf("Bus Controller:\n");
    printf("  Messages Sent: %d\n", bc_sent);
    printf("  Messages Received: %d\n", bc_received);
    printf("  Errors: %d\n", bc_errors);
    
    printf("Remote Terminal:\n");
    printf("  Messages Received: %d\n", rt_received);
    printf("  Messages Transmitted: %d\n", rt_transmitted);
    printf("  Errors: %d\n", rt_errors);
    printf("==============================\n\n");
}

int main() {
    printf("1553B Communication Protocol Example\n");
    printf("====================================\n\n");
    
    // Initialize random seed
    srand(time(NULL));
    
    // Configure 1553B system
    mil_std_1553b_config_t config = {
        .bus_controller_id = 1,
        .remote_terminal_id = 2,
        .bus_speed = 1000000, // 1 MHz
        .message_timeout_ms = 100
    };
    
    // Initialize bus controller
    bus_controller_t* bc = bc_init(config.bus_controller_id, &config);
    if (!bc) {
        printf("Failed to initialize bus controller\n");
        return -1;
    }
    
    // Initialize remote terminal
    remote_terminal_t* rt = rt_init(config.remote_terminal_id, &config);
    if (!rt) {
        printf("Failed to initialize remote terminal\n");
        bc_cleanup(bc);
        return -1;
    }
    
    // Start both components
    if (!bc_start(bc)) {
        printf("Failed to start bus controller\n");
        rt_cleanup(rt);
        bc_cleanup(bc);
        return -1;
    }
    
    if (!rt_start(rt)) {
        printf("Failed to start remote terminal\n");
        bc_stop(bc);
        rt_cleanup(rt);
        bc_cleanup(bc);
        return -1;
    }
    
    printf("1553B system started successfully\n");
    printf("Bus Controller ID: %d\n", config.bus_controller_id);
    printf("Remote Terminal ID: %d\n", config.remote_terminal_id);
    printf("Bus Speed: %d Hz\n", config.bus_speed);
    printf("\n");
    
    // Main communication loop
    float time = 0.0f;
    const float time_step = 0.1f;
    const int max_iterations = 50;
    
    for (int i = 0; i < max_iterations; i++) {
        printf("=== Iteration %d (Time: %.1f s) ===\n", i + 1, time);
        
        // Generate new position and attitude data
        position_data_t position;
        attitude_data_t attitude;
        
        generate_position_data(&position, time);
        generate_attitude_data(&attitude, time);
        
        printf("Generated Data:\n");
        printf("  Position: X=%.2f m, Y=%.2f m\n", position.x_position, position.y_position);
        printf("  Attitude: Roll=%.4f rad, Pitch=%.4f rad\n", attitude.roll, attitude.pitch);
        
        // Update remote terminal with new data
        rt_update_position(rt, &position);
        rt_update_attitude(rt, &attitude);
        
        // Send data request to remote terminal (subaddress 1)
        printf("Sending data request to RT %d, subaddress 1...\n", config.remote_terminal_id);
        bool success = bc_send_position_attitude(bc, config.remote_terminal_id, 1, &position, &attitude);
        
        if (success) {
            printf("Data request queued successfully\n");
        } else {
            printf("Failed to queue data request\n");
        }
        
        // Send data update to remote terminal (subaddress 2)
        printf("Sending data update to RT %d, subaddress 2...\n", config.remote_terminal_id);
        success = bc_send_position_attitude(bc, config.remote_terminal_id, 2, &position, &attitude);
        
        if (success) {
            printf("Data update queued successfully\n");
        } else {
            printf("Failed to queue data update\n");
        }
        
        // Print remote terminal status
        print_rt_status(rt);
        
        // Wait for message processing
        usleep(100000); // 100ms delay
        
        time += time_step;
        printf("\n");
    }
    
    // Print final statistics
    print_system_statistics(bc, rt);
    
    // Cleanup
    printf("Stopping 1553B system...\n");
    bc_stop(bc);
    rt_stop(rt);
    
    // Wait for threads to finish
    usleep(100000); // 100ms
    
    rt_cleanup(rt);
    bc_cleanup(bc);
    
    printf("1553B system stopped successfully\n");
    
    return 0;
}