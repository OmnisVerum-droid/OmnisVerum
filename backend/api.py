"""
Vercel serverless entry point for Omnisverum V1
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from main import app

# Export the app for Vercel
app_handler = app

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler."""
    return app_handler(request)
