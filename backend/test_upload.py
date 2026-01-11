"""Quick test script to diagnose upload issues

NOTE: This is an integration script that expects a running backend on localhost:8000.
Pytest will try to import any `test_*.py` file, so we explicitly skip it during pytest runs.
"""

import pytest

pytest.skip("Integration script (requires running backend). Skipped during pytest.", allow_module_level=True)

import requests
import os

# Test if backend is running
try:
    response = requests.get("http://localhost:8000/health")
    print(f"✅ Backend health check: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"❌ Backend not reachable: {e}")
    exit(1)

# Check uploads directory
uploads_dir = "uploads"
if os.path.exists(uploads_dir):
    print(f"✅ Uploads directory exists: {os.path.abspath(uploads_dir)}")
else:
    print(f"❌ Uploads directory missing: {os.path.abspath(uploads_dir)}")
    os.makedirs(uploads_dir, exist_ok=True)
    print(f"✅ Created uploads directory")

# Check if we can write to uploads
test_file = os.path.join(uploads_dir, "test.txt")
try:
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    print(f"✅ Can write to uploads directory")
except Exception as e:
    print(f"❌ Cannot write to uploads directory: {e}")

# Check DIP debug output directory
dip_dir = "dip_debug_output"
if os.path.exists(dip_dir):
    print(f"✅ DIP debug directory exists: {os.path.abspath(dip_dir)}")
else:
    print(f"⚠️ DIP debug directory doesn't exist (will be created on first upload)")

print("\n✅ All basic checks passed!")
print("If upload still fails, check backend terminal for error messages.")

