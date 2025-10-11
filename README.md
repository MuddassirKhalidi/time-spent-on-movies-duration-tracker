# 🎬 Movie Time Tracker

A beautiful web application to track the time you spend watching movies and TV series. Built with HTML, CSS, JavaScript for the frontend and FastAPI for the backend.

## Features

- 🔍 **Smart Search**: Search for movies and series with real-time autocomplete suggestions
- 📊 **Time Tracking**: Visual progress bar showing total watch time with detailed statistics
- 📝 **Watched List**: Keep track of all movies and series you've watched
- 🎨 **Modern UI**: Beautiful, responsive design with smooth animations
- ⚡ **Fast & Simple**: Lightweight backend with in-memory storage

## Project Structure

```
test-repo/
├── backend/
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── index.html        # Main HTML file
│   ├── style.css         # Styles and animations
│   └── script.js         # Frontend logic
└── README.md
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser

## Installation & Setup

### 1. Get OMDb API Key (Required)

1. Visit [omdbapi.com](http://www.omdbapi.com/) and sign up for a free account
2. Get your API key (looks like: `12345678`)
3. Create a `.env` file in the backend directory:
   ```bash
   cd backend
   echo "OMDB_API_KEY=your_actual_api_key_here" > .env
   ```

### 2. Install Backend Dependencies

Navigate to the backend directory and install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the Backend Server

Run the FastAPI server:

```bash
python main.py
```

The backend API will start running at `http://localhost:8000`

You can access the API documentation at `http://localhost:8000/docs`

### 4. Open the Frontend

Simply open the `frontend/index.html` file in your web browser:

```bash
# From the project root
open frontend/index.html
```

Or you can serve it with a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then navigate to `http://localhost:8080` in your browser.

## Usage

1. **Search for a Movie/Series**: 
   - Type in the search bar
   - See real-time suggestions appear
   - Click on a result to add it to your watched list

2. **View Statistics**:
   - See your total watch time in minutes, hours, and days
   - Track the number of movies/series you've watched
   - Watch the progress bar grow towards 100 hours goal

3. **Manage Watched List**:
   - View all movies and series you've added
   - See when you added each item
   - Remove items using the "Remove" button

## API Endpoints

### GET `/api/search?q={query}`
Search for movies by title
- **Query Parameters**: `q` (search query)
- **Returns**: List of matching movies/series

### POST `/api/watched`
Add a movie to the watched list
- **Body**: `{ "movie_id": number }`
- **Returns**: Success status and movie details

### GET `/api/watched`
Get all watched movies
- **Returns**: List of watched movies with timestamps

### GET `/api/stats`
Get viewing statistics
- **Returns**: Total minutes, hours, days, and count

### DELETE `/api/watched/{movie_id}`
Remove a movie from watched list
- **Returns**: Success status

## OMDb API Integration

The application uses the OMDb (Open Movie Database) API to provide access to millions of movies and TV series. This includes:

- Real-time search through the entire OMDb database
- Accurate runtime duration information
- Rich movie metadata (plot, genre, director, actors)
- High-quality movie posters
- Both movies and TV series support

**Note**: You need a free OMDb API key to use this application. See `OMDB_SETUP.md` for setup instructions.

## Technical Details

### Backend (FastAPI)
- RESTful API with CORS enabled
- In-memory data storage (resets on restart)
- Pydantic models for data validation
- Automatic API documentation with Swagger

### Frontend
- Vanilla JavaScript (no frameworks required)
- Responsive CSS Grid layout
- Smooth animations and transitions
- Real-time search with debouncing
- Toast notifications for user feedback

## Customization

### Change the Time Goal
Edit the `goalHours` variable in `frontend/script.js`:
```javascript
const goalHours = 100; // Change to your desired goal
```

### Add More Movies
Add entries to the `MOVIES_DB` list in `backend/main.py`:
```python
{"id": 31, "title": "Your Movie", "year": 2024, "duration": 120, "type": "movie"}
```

### Customize Colors
Edit CSS variables in `frontend/style.css`:
```css
:root {
    --primary-color: #6366f1;
    --bg-color: #0f172a;
    /* ... other colors */
}
```

## Notes

- **OMDb API Key Required**: The application requires a valid OMDb API key to function
- **Rate Limits**: Free OMDb accounts have a 1,000 requests/day limit
- **In-Memory Storage**: The backend uses in-memory storage, so data will be lost when the server restarts
- **Internet Required**: The application needs internet connection to access OMDb API
- **No Fallback**: Unlike the previous version, there's no static database fallback - OMDb API is required

## Future Enhancements

- Persistent database storage
- User authentication
- Multiple user profiles
- Export statistics to CSV/PDF
- Import from IMDb/TMDB
- Add ratings and reviews
- Filtering and sorting options

## License

This project is open source and available for personal use.

---

Made with ❤️ for movie lovers

