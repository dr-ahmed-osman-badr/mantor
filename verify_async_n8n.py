import datetime
import time
import requests
import logging
from unittest.mock import patch, MagicMock
from life_manager.services import N8nIntegrationService

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_async_behavior():
    print("--- Testing Async N8n Integration ---")

    # Mock requests.post to simulate a slow response
    with patch('requests.post') as mock_post:
        # Simulate a 2-second network delay
        def side_effect(*args, **kwargs):
            time.sleep(2)
            mock_response = MagicMock()
            mock_response.status_code = 200
            return mock_response
        
        mock_post.side_effect = side_effect

        print("Triggering chat response (should return immediately)...")
        start_time = time.time()
        
        # Call the service method
        N8nIntegrationService.trigger_chat_response("test_session", "Hello")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Function returned in {duration:.4f} seconds")

        if duration < 0.1:
            print("SUCCESS: Function returned immediately (Async work confirmed).")
        else:
            print(f"FAILURE: Function took too long ({duration:.4f}s). Is it synchronous?")

        # Wait for the thread to complete
        print("Waiting for thread to complete (simulated backend work)...")
        time.sleep(2.5) 
        
        if mock_post.called:
            print("SUCCESS: requests.post was called in the background.")
        else:
            print("FAILURE: requests.post was NOT called.")

test_async_behavior()
