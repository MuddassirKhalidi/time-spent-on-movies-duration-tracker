# 🎬 OMDb API Setup Guide

## What is OMDb API?

The OMDb API (Open Movie Database) provides access to movie and TV series information including:
- Movie titles, years, and genres
- Runtime duration (in minutes)
- Plot summaries
- Director and actor information
- IMDb ratings
- Poster images

## Getting Your API Key

1. **Visit OMDb API Website**: Go to [http://www.omdbapi.com/](http://www.omdbapi.com/)

2. **Sign Up**: Click "Get API Key" and create a free account

3. **Get Your Key**: Once registered, you'll receive an API key (looks like: `12345678`)

## Setting Up the API Key

### Method 1: Environment Variable (Recommended)

1. **Create a `.env` file** in the `backend` directory:
   ```bash
   cd backend
   touch .env
   ```

2. **Add your API key** to the `.env` file:
   ```
   OMDB_API_KEY=your_actual_api_key_here
   ```

3. **Replace** `your_actual_api_key_here` with your actual OMDb API key

### Method 2: Direct Configuration

Edit the `backend/main.py` file and replace this line:
```python
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "demo")
```

With:
```python
OMDB_API_KEY = "your_actual_api_key_here"
```

## API Usage Limits

- **Free Tier**: 1,000 requests per day
- **Paid Plans**: Available for higher limits

## Testing Your Setup

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Backend**:
   ```bash
   python main.py
   ```

3. **Test the Search**: Open your frontend and try searching for movies like:
   - "The Matrix"
   - "Breaking Bad"
   - "Inception"

## Troubleshooting

### "Invalid API Key" Error
- Double-check your API key in the `.env` file
- Make sure there are no extra spaces or quotes around the key
- Verify the key is active on the OMDb website

### No Search Results
- Check your internet connection
- Verify the OMDb API is accessible
- The app will fall back to the static database if OMDb fails

### Rate Limit Exceeded
- You've hit the 1,000 requests/day limit
- Wait 24 hours or upgrade to a paid plan
- The app will fall back to static movies

## Features Added

With OMDb integration, your movie tracker now includes:

✅ **Real-time Movie Search**: Search millions of movies and TV series
✅ **Accurate Runtime Data**: Get precise duration information
✅ **Rich Movie Details**: Plot, genre, director, actors
✅ **Poster Images**: Movie posters (if available)
✅ **Fallback System**: Uses static database if OMDb is unavailable

## Example Search Results

When you search for "The Matrix", you'll now get:
- **Title**: The Matrix
- **Year**: 1999
- **Duration**: 136 minutes
- **Genre**: Action, Sci-Fi
- **Director**: Lana Wachowski, Lilly Wachowski
- **Plot**: A computer hacker learns about the true nature of reality...

---

**Note**: The app works without an API key using the static database, but you'll get much richer data with OMDb integration!

