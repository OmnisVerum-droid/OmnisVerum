"""
Vercel serverless entry point for Omnisverum V1
"""
import sys
import os
from fastapi import Request
from fastapi.responses import JSONResponse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from main import app

# Vercel serverless function handler
async def handler(request):
    """Vercel serverless function handler."""
    try:
        # Convert Vercel request to FastAPI request
        scope = {
            'type': 'http',
            'method': request.method,
            'path': request.url.path,
            'query_string': request.url.query.encode(),
            'headers': dict(request.headers),
        }
        
        # Get the ASGI application
        asgi_app = app
        
        # Create receive function
        async def receive():
            return {'body': request.body, 'type': 'http.request'}
        
        # Create send function
        response_sent = {}
        async def send(message):
            if message['type'] == 'http.response.start':
                response_sent['status'] = message['status']
                response_sent['headers'] = message.get('headers', [])
            elif message['type'] == 'http.response.body':
                response_sent['body'] = message.get('body', b'')
        
        # Call the ASGI app
        await asgi_app(scope, receive, send)
        
        return JSONResponse(
            content={'message': 'Server running'},
            status=response_sent.get('status', 200)
        )
    except Exception as e:
        return JSONResponse(
            content={'error': str(e)},
            status=500
        )
