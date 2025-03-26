import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/audio-stream/"  # Update WebSocket URL to match routing
    async with websockets.connect(uri) as websocket:
        # Send a message (ensure that your server consumer handles it accordingly)
        message = {
            "event": "start",  # This should match your consumer logic
            "start": {"streamSid": "test-stream-123"}  # Additional data to pass with the event
        }
        await websocket.send(json.dumps(message))  # Send the message
        
        # Receive a response from the WebSocket server
        response = await websocket.recv()  # Receive message from server
        print("Response:", response)  # Print the received response

# Run the WebSocket connection test
asyncio.get_event_loop().run_until_complete(test_websocket())
