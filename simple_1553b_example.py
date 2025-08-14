#!/usr/bin/env python3
"""
Simple 1553B Communication Protocol Example
Demonstrates position and attitude data transmission
"""

from protocol_1553b_example import (
    CommunicationProtocol, PositionData, AttitudeData
)
import time

def main():
    print("=== Simple 1553B Protocol Example ===\n")
    
    # Create communication protocol
    protocol = CommunicationProtocol()
    
    # Add remote terminals for different systems
    nav_system = protocol.add_remote_terminal(1, "Navigation_System")
    guidance_system = protocol.add_remote_terminal(2, "Guidance_System")
    control_system = protocol.add_remote_terminal(3, "Control_System")
    
    # Start communication
    protocol.start_communication()
    
    try:
        print("1. Sending Position Data to Navigation System...")
        position = PositionData(100.5, 200.3, 1500.7)
        protocol.send_position_data(1, position)
        time.sleep(0.01)
        
        print("2. Sending Attitude Data to Guidance System...")
        attitude = AttitudeData(15.5, 2.3, 45.7)
        protocol.send_attitude_data(2, attitude)
        time.sleep(0.01)
        
        print("3. Broadcasting Position to All Systems...")
        broadcast_position = PositionData(102.8, 199.5, 1500.9)
        protocol.broadcast_position(broadcast_position)
        time.sleep(0.01)
        
        print("4. Broadcasting Attitude to All Systems...")
        broadcast_attitude = AttitudeData(15.8, 2.2, 45.9)
        protocol.broadcast_attitude(broadcast_attitude)
        time.sleep(0.01)
        
        print("\n5. System Status:")
        print("-" * 40)
        for rt_address in [1, 2, 3]:
            status = protocol.get_rt_status(rt_address)
            if status:
                print(f"RT {status['address']} ({status['name']}):")
                print(f"  Status: {status['status']}")
                print(f"  Position: {status['position']}")
                print(f"  Attitude: {status['attitude']}")
                print()
        
        print("6. Data Retrieval Example:")
        print("-" * 30)
        pos_data = protocol.bus_controller.request_position_data(1)
        att_data = protocol.bus_controller.request_attitude_data(2)
        
        if pos_data:
            print(f"Retrieved position from Navigation System: {pos_data}")
        if att_data:
            print(f"Retrieved attitude from Guidance System: {att_data}")
        
        print("\nProtocol demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        protocol.stop_communication()

if __name__ == "__main__":
    main()