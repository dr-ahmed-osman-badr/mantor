import datetime
import time
import requests
import logging
from unittest.mock import patch, MagicMock
from life_manager.services import N8nIntegrationService

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_async_behavior():
    print("--- Testing Async N8n Integration (With Response Handling) ---")

    # Mock requests.post to simulate a slow response + JSON return
    with patch('requests.post') as mock_post, patch('life_manager.models.ChatMessage.objects.create') as mock_create_msg:
        # Simulate a 1-second network delay
        def side_effect(*args, **kwargs):
            time.sleep(1)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "This is a mock AI reply."}
            return mock_response
        
        mock_post.side_effect = side_effect

        print("Triggering chat response (should return immediately)...")
        start_time = time.time()
        
        # Call the service method
        N8nIntegrationService.trigger_chat_response(123, "Hello AI") # session_id=123
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Function returned in {duration:.4f} seconds")

        if duration < 0.1:
            print("SUCCESS: Function returned immediately (Async work confirmed).")
        else:
            print(f"FAILURE: Function took too long ({duration:.4f}s). Is it synchronous?")

        # Wait for the thread to complete
        print("Waiting for thread to complete (simulated backend work)...")
        time.sleep(1.5) 
        
        if mock_post.called:
            print("SUCCESS: requests.post was called in the background.")
        else:
            print("FAILURE: requests.post was NOT called.")

        if mock_create_msg.called:
            print("SUCCESS: ChatMessage.objects.create was called with the AI response.")
            # Verify args if needed
            args, kwargs = mock_create_msg.call_args
            if kwargs.get('content') == "This is a mock AI reply.":
                 print("SUCCESS: Content matches mock response.")
            else:
                 print(f"FAILURE: Content mismatch. Got: {kwargs.get('content')}")
        else:
             print("FAILURE: ChatMessage.objects.create was NOT called.")

test_async_behavior()
