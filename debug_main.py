#!/usr/bin/env python3
import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("Command line args:", sys.argv)

# Try to import and run main
try:
    print("Attempting to import main...")
    import main
    print("Import successful!")
    
    # Test the main function
    print("Testing main function...")
    sys.argv = ['main.py', 'status']
    result = main.main()
    print(f"Main function returned: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
