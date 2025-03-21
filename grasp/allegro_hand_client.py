#!/usr/bin/env python3

import socket
import time
import numpy as np
import subprocess
import os
import signal
import atexit
import sys

class AllegroHand:
    def __init__(self, host='localhost', port=12321, grasp_path=None):
        """Initialize connection to Allegro Hand server
        
        Args:
            host: Server hostname
            port: Server port
            grasp_path: Path to the grasp executable. If None, will try to find it
        """
        self.host = host
        self.port = port
        self.socket = None
        self.grasp_process = None
        
        # Find grasp executable
        if grasp_path is None:
            # Try common locations
            possible_paths = [
                './grasp',
                '../build/grasp/grasp',
                'grasp/grasp',
                os.path.join(os.path.dirname(__file__), 'grasp')
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    grasp_path = path
                    break
            if grasp_path is None:
                raise FileNotFoundError("Could not find grasp executable. Please specify path.")
        
        self.grasp_path = os.path.abspath(grasp_path)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        
        # Start grasp program
        self.start_grasp()
        
        # Wait a bit for the server to start
        time.sleep(2)
        
        # Connect to the server
        self.connect()
        
    def start_grasp(self):
        """Start the grasp program"""
        try:
            print(f"Starting {self.grasp_path}...")
            # Start process and redirect output to /dev/null
            with open(os.devnull, 'w') as devnull:
                self.grasp_process = subprocess.Popen(
                    self.grasp_path,
                    stdout=devnull,
                    stderr=devnull,
                    preexec_fn=os.setsid  # Create new process group
                )
        except Exception as e:
            print(f"Failed to start grasp program: {e}")
            sys.exit(1)
        
    def cleanup(self):
        """Cleanup resources"""
        if self.socket:
            try:
                # Try to send a quit command to the grasp program
                self.socket.send("QUIT\n".encode())
                time.sleep(0.1)  # Give it a moment to process
            except:
                pass  # Ignore any socket errors during cleanup
            self.close()
        
        if self.grasp_process:
            try:
                # Check if process is still running
                if self.grasp_process.poll() is None:
                    # Process is still running, try to terminate it gracefully
                    os.killpg(os.getpgid(self.grasp_process.pid), signal.SIGTERM)
                    try:
                        self.grasp_process.wait(timeout=2)  # Wait up to 2 seconds
                    except subprocess.TimeoutExpired:
                        # If still running after SIGTERM, force kill
                        if self.grasp_process.poll() is None:
                            os.killpg(os.getpgid(self.grasp_process.pid), signal.SIGKILL)
            except ProcessLookupError:
                # Process is already gone, which is fine
                pass
            except Exception as e:
                # Log other errors but don't raise
                print(f"Warning during cleanup: {e}", file=sys.stderr)
            finally:
                self.grasp_process = None
        
    def connect(self):
        """Connect to the Allegro Hand server"""
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                print(f"Connected to Allegro Hand server at {self.host}:{self.port}")
                return
            except Exception as e:
                attempt += 1
                if attempt < max_attempts:
                    print(f"Connection attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(1)
                else:
                    print(f"Failed to connect after {max_attempts} attempts: {e}")
                    self.cleanup()
                    sys.exit(1)
            
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
    hand = AllegroHand(grasp_path='/home/lixin/Downloads/Allegro_Hand_V4/allegro_hand_linux_v4/build/grasp/grasp')
    
    try:
        # Example 1: Make a fist
        fist = np.array([
            0.0, 0.5, 0.5, 0.5,  # Finger 1
            0.0, 0.5, 0.5, 0.5,  # Finger 2
            0.0, 0.5, 0.5, 0.5,  # Finger 3
            0.2976, 0.9034, 0.7929, 0.6017   # Thumb
        ])
        
        print("Making a fist...")
        hand.set_joint_positions(fist)
        time.sleep(2)
        
        # Example 2: Open hand
        open_hand = np.zeros(16)  # All joints at 0 position
        print("Opening hand...")
        hand.set_joint_positions(open_hand)
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        print("Cleaning up...")
        hand.cleanup()
        # Give some time for the C++ program to clean up
        time.sleep(1)

if __name__ == "__main__":
    demo()