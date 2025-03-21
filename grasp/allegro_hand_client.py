#!/usr/bin/env python3

import socket
import time
import numpy as np

class AllegroHand:
    def __init__(self, host='localhost', port=12321):
        """Initialize connection to Allegro Hand server"""
        self.host = host
        self.port = port
        self.socket = None
        self.connect()
        
    def connect(self):
        """Connect to the Allegro Hand server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to Allegro Hand server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.socket = None
            
    def set_joint_positions(self, positions):
        """Set joint positions for all joints
        
        Args:
            positions: List/array of 16 joint angles in radians
        """
        if len(positions) != 16:
            raise ValueError("Must provide exactly 16 joint positions")
            
        if not self.socket:
            print("Not connected to server")
            return False
            
        try:
            # Format command string
            cmd = "SET_JOINTS " + " ".join([f"{p:.6f}" for p in positions]) + "\n"
            self.socket.send(cmd.encode())
            
            # Wait for acknowledgment
            response = self.socket.recv(1024).decode().strip()
            return response == "OK"
        except Exception as e:
            print(f"Failed to send joint positions: {e}")
            return False
            
    def close(self):
        """Close connection to server"""
        if self.socket:
            self.socket.close()
            self.socket = None

def demo():
    """Demo showing basic usage"""
    hand = AllegroHand()
    
    # Example 1: Make a fist
    fist = np.array([
        1.2068, 1.0, 1.4042, -0.1194,  # Finger 1
        1.2481, 1.4073, 0.8163, -0.0093,  # Finger 2
        1.2712, 1.3881, 1.0122, 0.1116,  # Finger 3
        0.2976, 0.9034, 0.7929, 0.6017   # Thumb
    ])
    
    print("Making a fist...")
    hand.set_joint_positions(fist)
    time.sleep(2)
    
    # Example 2: Open hand
    open_hand = np.zeros(16)  # All joints at 0 position
    print("Opening hand...")
    hand.set_joint_positions(open_hand)
    
    hand.close()

if __name__ == "__main__":
    demo() 