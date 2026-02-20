#!/usr/bin/env python3
"""
Simple startup script for VOCA AI server
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the main app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
