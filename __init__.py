# Root package initialization
"""
Strategic Intelligence System
============================
AI-powered strategic intelligence with Gmail integration and Claude analysis
"""

# Ensure the project root is in the Python path
import sys
import os

# Add the current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

__version__ = "1.0.0"
__author__ = "Strategic Intelligence Team" 