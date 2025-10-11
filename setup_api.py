#!/usr/bin/env python3
"""
Setup script to configure OMDb API key
"""

import os

def setup_api_key():
    """Interactive setup for OMDb API key"""
    
    print("🎬 OMDb API Key Setup")
    print("=" * 50)
    
    print("\nTo use the Movie Time Tracker, you need a free OMDb API key:")
    print("1. Visit: http://www.omdbapi.com/")
    print("2. Click 'Get API Key' and sign up for free")
    print("3. Copy your API key (looks like: 12345678)")
    
    print("\n" + "=" * 50)
    
    api_key = input("\nEnter your OMDb API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return False
    
    # Create .env file in backend directory
    backend_dir = "backend"
    env_file = os.path.join(backend_dir, ".env")
    
    try:
        # Create backend directory if it doesn't exist
        os.makedirs(backend_dir, exist_ok=True)
        
        # Write .env file
        with open(env_file, 'w') as f:
            f.write(f"OMDB_API_KEY={api_key}\n")
        
        print(f"✅ API key saved to {env_file}")
        
        # Test the key
        print("\n🔍 Testing your API key...")
        
        # Import and run test
        import subprocess
        result = subprocess.run(["python", "test_api.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ API key is working correctly!")
            print("\n🚀 You can now start your backend server:")
            print("   cd backend")
            print("   python main.py")
            return True
        else:
            print("❌ API key test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up API key: {e}")
        return False

if __name__ == "__main__":
    setup_api_key()

