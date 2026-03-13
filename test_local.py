import os
from dotenv import load_dotenv

# Load variables from .env if it exists
load_dotenv()

# Set dummy password if missing just to see if SerpApi works
# In a real run, this would fail the email step
if not os.environ.get("GMAIL_APP_PASSWORD"):
    print("Warning: GMAIL_APP_PASSWORD is not set. Email will fail, but we can still test the API logic.")
    os.environ["GMAIL_APP_PASSWORD"] = "dummy_password"

# Import our cloud function
from main import gift_agent

class MockRequest:
    """A minimal mock of the Flask request object that Cloud Functions use."""
    def __init__(self, json_data=None, args=None):
        self._json_data = json_data or {}
        self.args = args or {}
        
    def get_json(self, silent=False):
        return self._json_data

def run_local_test():
    print("=== Starting Local Cloud Function Test ===")
    
    # Create the mock request
    request = MockRequest()
    
    # Run the function
    try:
        response, status_code = gift_agent(request)
        print("\n=== Test Results ===")
        print(f"Status Code: {status_code}")
        print(f"Response Body: {response}")
    except Exception as e:
        print(f"\nFunction crashed during test:")
        print(e)
        
if __name__ == "__main__":
    run_local_test()
