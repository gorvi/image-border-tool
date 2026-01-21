
import sys
import os

# Ensure we can import auth_manager
sys.path.append(os.getcwd())

try:
    from auth_manager import auth
except ImportError as e:
    print(f"Error importing auth_manager: {e}")
    print("Please ensure requests and cryptography are installed.")
    sys.exit(1)

def test_activation(code):
    print(f"--- Client Activation Test ---")
    print(f"Machine ID: {auth.machine_code}")
    print(f"Attempting to activate with code: {code}")
    
    success, msg = auth.activate_online(code)
    
    print(f"\nResult: {'✅ Success' if success else '❌ Failed'}")
    print(f"Message: {msg}")
    
    if success:
        status = auth.get_status()
        print(f"New Status: {status}")
        
        # Verify persistence
        print("\nVerifying LOCAL persistence...")
        # Reload auth
        auth.data = auth._load_data()
        if auth.data.get('is_activated'):
            print("✅ License saved to disk")
            print(f"   Signature: {auth.data.get('signature')[:20]}...")
        else:
            print("❌ License NOT saved")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <LICENSE_KEY>")
        sys.exit(1)
        
    test_activation(sys.argv[1])
