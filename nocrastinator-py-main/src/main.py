"""
Main entry point for the Productivity Tracker application.
"""

import os
import sys
from app import main

if __name__ == "__main__":
    # Make sure the data directory exists
    from config import DATA_DIRECTORY
    os.makedirs(DATA_DIRECTORY, exist_ok=True)
    
    # Launch the application
    main() 