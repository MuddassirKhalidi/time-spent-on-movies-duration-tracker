from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file in backend directory
load_dotenv(".env")

app = FastAPI()

# OMDb API configuration
OMDB_API_KEY = os.getenv("OMDB_API_KEY")  # Use "demo" as fallback
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No static database - using OMDb API only

# In-memory storage for watched movies
watched_movies = []

class Movie(BaseModel):
    id: int
    title: str
    year: int
    duration: int
    type: str

class WatchedMovie(BaseModel):
    movie: Movie
    watched_at: str

class AddMovieRequest(BaseModel):
    movie_id: str  # Changed to string to handle OMDb IDs

class OMDBMovie(BaseModel):
    title: str
    year: str
    runtime: str
    type: str
    imdb_id: str
    poster: str = ""

@app.get("/")
def read_root():
    return {"message": "Movie Time Tracker API"}

@app.get("/api/test")
async def test_omdb():
    """Test OMDb API connection"""
    if not OMDB_API_KEY:
        return {"error": "OMDb API key not configured"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                OMDB_BASE_URL,
                params={
                    "s": "The Matrix",
                    "apikey": OMDB_API_KEY
                }
            )
            data = response.json()
            return {
                "api_key_configured": True,
                "api_key_preview": OMDB_API_KEY[:8] + "...",
                "test_search_status": response.status_code,
                "test_search_result": data
            }
    except Exception as e:
        return {
            "api_key_configured": True,
            "api_key_preview": OMDB_API_KEY[:8] + "...",
            "error": str(e)
        }

# Helper function to parse runtime from OMDb response
def parse_runtime(runtime_str: str) -> int:
    """Parse runtime string like '142 min' to minutes"""
    if not runtime_str or runtime_str == "N/A":
        return 0
    
    # Extract number from runtime string
    match = re.search(r'(\d+)', runtime_str)
    if match:
        return int(match.group(1))
    return 0

# Helper function to get movie details from OMDb
async def get_movie_details(imdb_id: str) -> Dict[str, Any]:
    """Get detailed movie information from OMDb API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                OMDB_BASE_URL,
                params={
                    "i": imdb_id,
                    "apikey": OMDB_API_KEY
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return {}

# Search movies using OMDb API
async def search_omdb_movies(query: str) -> List[Dict[str, Any]]:
    """Search for movies using OMDb API"""
    try:
        print(f"Searching OMDb for: '{query}' with API key: {OMDB_API_KEY[:8]}..." if OMDB_API_KEY else "No API key")
        
        async with httpx.AsyncClient() as client:
            # First, search for movies
            search_response = await client.get(
                OMDB_BASE_URL,
                params={
                    "s": query,
                    "apikey": OMDB_API_KEY,
                    "type": "movie"
                }
            )
            
            print(f"Search response status: {search_response.status_code}")
            search_data = search_response.json()
            print(f"Search data: {search_data}")
            
            if search_data.get("Response") == "False":
                print(f"OMDb API returned False: {search_data.get('Error', 'Unknown error')}")
                return []
            
            search_results = search_data.get("Search", [])
            print(f"Found {len(search_results)} search results")
            
            # Get detailed information for each movie (limited to first 5)
            detailed_results = []
            for movie in search_results[:5]:
                imdb_id = movie.get("imdbID")
                if imdb_id:
                    details = await get_movie_details(imdb_id)
                    if details.get("Response") == "True":
                        detailed_results.append({
                            "id": f"omdb_{imdb_id}",  # Unique ID for OMDb movies
                            "title": details.get("Title", ""),
                            "year": details.get("Year", ""),
                            "duration": parse_runtime(details.get("Runtime", "")),
                            "type": "movie" if details.get("Type") == "movie" else "series",
                            "imdb_id": imdb_id,
                            "poster": details.get("Poster", ""),
                            "plot": details.get("Plot", ""),
                            "genre": details.get("Genre", ""),
                            "director": details.get("Director", ""),
                            "actors": details.get("Actors", "")
                        })
            
            print(f"Returning {len(detailed_results)} detailed results")
            return detailed_results
            
    except Exception as e:
        print(f"Error searching OMDb: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/api/search")
async def search_movies(q: str = ""):
    """Search movies by title using OMDb API only"""
    if not q:
        return []
    
    # Check if API key is configured
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="OMDb API key not configured. Please add OMDB_API_KEY to your environment variables."
        )
    
    # Search using OMDb API only
    omdb_results = await search_omdb_movies(q)
    
    if not omdb_results:
        raise HTTPException(
            status_code=404, 
            detail=f"No movies found for '{q}'. Please check your search term or try a different query."
        )
    
    return omdb_results

@app.post("/api/watched")
async def add_watched_movie(request: AddMovieRequest):
    """Add a movie to watched list (OMDb movies only)"""
    movie_id = request.movie_id
    
    # Check if API key is configured
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="OMDb API key not configured. Please add OMDB_API_KEY to your environment variables."
        )
    
    # Only handle OMDb movies (all movies now come from OMDb)
    if not movie_id.startswith("omdb_"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid movie ID format. Only OMDb movies are supported."
        )
    
    # Fetch full movie details from OMDb
    imdb_id = movie_id.replace("omdb_", "")
    movie_details = await get_movie_details(imdb_id)
    
    if movie_details.get("Response") == "True":
        movie = {
            "id": movie_id,
            "title": movie_details.get("Title", ""),
            "year": movie_details.get("Year", ""),
            "duration": parse_runtime(movie_details.get("Runtime", "")),
            "type": "movie" if movie_details.get("Type") == "movie" else "series",
            "imdb_id": imdb_id,
            "poster": movie_details.get("Poster", ""),
            "plot": movie_details.get("Plot", ""),
            "genre": movie_details.get("Genre", ""),
            "director": movie_details.get("Director", ""),
            "actors": movie_details.get("Actors", ""),
            "is_omdb": True
        }
        
        # Check if movie is already in watched list
        existing_movie = next(
            (entry for entry in watched_movies if entry["movie"]["imdb_id"] == imdb_id), 
            None
        )
        
        if existing_movie:
            raise HTTPException(
                status_code=409, 
                detail=f"Movie '{movie['title']}' is already in your watched list."
            )
        
        watched_entry = {
            "movie": movie,
            "watched_at": datetime.now().isoformat()
        }
        watched_movies.append(watched_entry)
        
        return {"success": True, "movie": movie}
    else:
        raise HTTPException(status_code=404, detail="Movie not found in OMDb")

@app.get("/api/watched")
def get_watched_movies():
    """Get all watched movies"""
    return watched_movies

@app.get("/api/stats")
def get_stats():
    """Get total time spent watching"""
    total_minutes = sum(entry["movie"]["duration"] for entry in watched_movies)
    total_count = len(watched_movies)
    
    return {
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "total_days": round(total_minutes / (60 * 24), 2),
        "total_count": total_count
    }

@app.delete("/api/watched/{movie_id}")
def remove_watched_movie(movie_id: str):
    """Remove a movie from watched list"""
    global watched_movies
    initial_length = len(watched_movies)
    watched_movies = [entry for entry in watched_movies if str(entry["movie"]["id"]) != movie_id]
    
    if len(watched_movies) < initial_length:
        return {"success": True}
    raise HTTPException(status_code=404, detail="Movie not found in watched list")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

