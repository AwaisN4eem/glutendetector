"""Quick test script to diagnose meal logging issues

NOTE: This is an integration script that expects a running backend on localhost:8000.
Pytest will try to import any `test_*.py` file, so we explicitly skip it during pytest runs.
"""

import pytest

pytest.skip("Integration script (requires running backend). Skipped during pytest.", allow_module_level=True)

import requests
import json

# Test meal logging endpoint
test_data = {
    "description": "had 3 eggs",
    "meal_type": "breakfast",
    "input_method": "text"
}

try:
    print("Testing meal logging endpoint...")
    response = requests.post(
        "http://localhost:8000/api/meals/?user_id=1",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("✅ Meal logged successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

