#!/usr/bin/env python3
"""
Test script to verify OMDb API key configuration
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv("backend/.env")

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_BASE_URL = "http://www.omdbapi.com/"

async def test_omdb_api():
    """Test OMDb API with the configured key"""
    
    print("🔍 Testing OMDb API Configuration")
    print("=" * 50)
    
    # Check if API key is configured
    if not OMDB_API_KEY:
        print("❌ ERROR: OMDb API key not configured!")
        print("\nTo fix this:")
        print("1. Get your API key from: http://www.omdbapi.com/")
        print("2. Create a .env file in the backend directory:")
        print("   echo 'OMDB_API_KEY=your_actual_api_key' > backend/.env")
        return False
    
    print(f"✅ API Key configured: {OMDB_API_KEY[:8]}...")
    
    # Test API connection
    try:
        async with httpx.AsyncClient() as client:
            print("\n🔍 Testing API connection...")
            
            # Test search
            response = await client.get(
                OMDB_BASE_URL,
                params={
                    "s": "The Matrix",
                    "apikey": OMDB_API_KEY
                }
            )
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("Response") == "True":
                    print("✅ API connection successful!")
                    print(f"📽️  Found {len(data.get('Search', []))} results for 'The Matrix'")
                    
                    # Show first result
                    if data.get("Search"):
                        first_movie = data["Search"][0]
                        print(f"🎬 First result: {first_movie.get('Title')} ({first_movie.get('Year')})")
                    
                    return True
                else:
                    print(f"❌ API Error: {data.get('Error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

async def test_movie_details():
    """Test getting detailed movie information"""
    
    if not OMDB_API_KEY:
        return
    
    print("\n🔍 Testing Movie Details...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get Matrix details
            response = await client.get(
                OMDB_BASE_URL,
                params={
                    "i": "tt0133093",  # The Matrix IMDb ID
                    "apikey": OMDB_API_KEY
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("Response") == "True":
                    print("✅ Movie details retrieved successfully!")
                    print(f"🎬 Title: {data.get('Title')}")
                    print(f"📅 Year: {data.get('Year')}")
                    print(f"⏱️  Runtime: {data.get('Runtime')}")
                    print(f"🎭 Genre: {data.get('Genre')}")
                    print(f"🎬 Director: {data.get('Director')}")
                else:
                    print(f"❌ Error getting movie details: {data.get('Error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎬 OMDb API Test Script")
    print("=" * 50)
    
    async def main():
        success = await test_omdb_api()
        if success:
            await test_movie_details()
            
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests passed! Your OMDb API is working correctly.")
            print("You can now start your backend server and use the movie tracker.")
        else:
            print("❌ Tests failed. Please check your API key configuration.")
    
    asyncio.run(main())
