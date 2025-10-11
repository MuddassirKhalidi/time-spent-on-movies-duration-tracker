// API Base URL
const API_URL = 'http://localhost:8000/api';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const watchedList = document.getElementById('watchedList');
const totalMinutesEl = document.getElementById('totalMinutes');
const totalHoursEl = document.getElementById('totalHours');
const totalDaysEl = document.getElementById('totalDays');
const totalCountEl = document.getElementById('totalCount');
const timeBar = document.getElementById('timeBar');
const timeBarText = document.getElementById('timeBarText');

// State
let searchTimeout = null;
let watchedMovies = [];

// Initialize app
async function init() {
    await loadWatchedMovies();
    await updateStats();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    searchInput.addEventListener('input', handleSearch);
    
    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.classList.remove('active');
        }
    });
}

// Handle search input
function handleSearch(e) {
    const query = e.target.value.trim();
    
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // If query is empty, hide results
    if (query.length === 0) {
        searchResults.classList.remove('active');
        return;
    }
    
    // Debounce search
    searchTimeout = setTimeout(() => {
        searchMovies(query);
    }, 300);
}

// Search movies via API
async function searchMovies(query) {
    try {
        const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const results = await response.json();
        displaySearchResults(results);
    } catch (error) {
        console.error('Error searching movies:', error);
        
        if (error.message.includes('API key not configured')) {
            showError('OMDb API key not configured. Please add your API key to the backend.');
        } else if (error.message.includes('No movies found')) {
            showError(`No movies found for "${query}". Try a different search term.`);
        } else {
            showError('Failed to search movies. Make sure the backend is running and your OMDb API key is configured.');
        }
    }
}

// Display search results
function displaySearchResults(results) {
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
        searchResults.classList.add('active');
        return;
    }
    
    searchResults.innerHTML = results.map(movie => `
        <div class="search-result-item" onclick="selectMovie('${movie.id}')">
            <div class="result-title">${movie.title}</div>
            <div class="result-info">
                ${movie.year} • 
                <span class="result-duration">${formatDuration(movie.duration)}</span>
                <span class="result-type">${movie.type}</span>
            </div>
        </div>
    `).join('');
    
    searchResults.classList.add('active');
}

// Select a movie from search results
async function selectMovie(movieId) {
    try {
        const response = await fetch(`${API_URL}/watched`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ movie_id: movieId }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Clear search
            searchInput.value = '';
            searchResults.classList.remove('active');
            
            // Reload watched movies and stats
            await loadWatchedMovies();
            await updateStats();
            
            // Show success feedback
            showSuccess(`Added "${data.movie.title}" to your watched list!`);
        }
    } catch (error) {
        console.error('Error adding movie:', error);
        
        if (error.message.includes('already in your watched list')) {
            showError(error.message);
        } else if (error.message.includes('API key not configured')) {
            showError('OMDb API key not configured. Please add your API key to the backend.');
        } else if (error.message.includes('Movie not found')) {
            showError('Movie not found. Please try searching again.');
        } else {
            showError('Failed to add movie. Make sure the backend is running and your OMDb API key is configured.');
        }
    }
}

// Load watched movies
async function loadWatchedMovies() {
    try {
        const response = await fetch(`${API_URL}/watched`);
        watchedMovies = await response.json();
        
        displayWatchedMovies();
    } catch (error) {
        console.error('Error loading watched movies:', error);
    }
}

// Display watched movies
function displayWatchedMovies() {
    if (watchedMovies.length === 0) {
        watchedList.innerHTML = `
            <div class="empty-state">
                <p>📽️ No movies watched yet</p>
                <p class="empty-subtitle">Start by searching and adding a movie above!</p>
            </div>
        `;
        return;
    }
    
    // Sort by watched date (most recent first)
    const sortedMovies = [...watchedMovies].reverse();
    
    watchedList.innerHTML = sortedMovies.map(entry => {
        const movie = entry.movie;
        const watchedDate = new Date(entry.watched_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        return `
            <div class="watched-item">
                <div class="watched-item-info">
                    <div class="watched-item-title">${movie.title}</div>
                    <div class="watched-item-details">
                        ${movie.year} • Added on ${watchedDate} •
                        <span class="watched-item-duration">${formatDuration(movie.duration)}</span>
                        <span class="watched-item-type">${movie.type}</span>
                    </div>
                </div>
                <button class="remove-btn" onclick="removeMovie('${movie.id}')">
                    Remove
                </button>
            </div>
        `;
    }).join('');
}

// Remove movie from watched list
async function removeMovie(movieId) {
    try {
        const response = await fetch(`${API_URL}/watched/${encodeURIComponent(movieId)}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (data.success) {
            await loadWatchedMovies();
            await updateStats();
            showSuccess('Movie removed from your watched list');
        }
    } catch (error) {
        console.error('Error removing movie:', error);
        showError('Failed to remove movie');
    }
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const stats = await response.json();
        
        console.log('Stats received:', stats); // Debug log
        
        // Get current values more reliably
        const currentMinutes = parseInt(totalMinutesEl.textContent) || 0;
        const currentHours = parseFloat(totalHoursEl.textContent) || 0;
        const currentDays = parseFloat(totalDaysEl.textContent) || 0;
        const currentCount = parseInt(totalCountEl.textContent) || 0;
        
        console.log('Current values:', { currentMinutes, currentHours, currentDays, currentCount }); // Debug log
        
        // Update stat cards with animation
        animateValue(totalMinutesEl, currentMinutes, stats.total_minutes, 500);
        animateValue(totalHoursEl, currentHours, stats.total_hours, 500);
        animateValue(totalDaysEl, currentDays, stats.total_days, 500);
        animateValue(totalCountEl, currentCount, stats.total_count, 500);
        
        // Update time bar (assuming 100 hours as goal)
        const goalHours = 100;
        const percentage = Math.min((stats.total_hours / goalHours) * 100, 100);
        timeBar.style.width = `${percentage}%`;
        timeBarText.textContent = `${stats.total_hours} hours`;
        
        // Show time bar text only if there's progress
        if (percentage > 0) {
            timeBarText.style.display = 'block';
        } else {
            timeBarText.style.display = 'none';
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Animate number changes
function animateValue(element, start, end, duration) {
    // Ensure start and end are valid numbers
    start = Number(start) || 0;
    end = Number(end) || 0;
    
    const isFloat = end % 1 !== 0;
    const range = end - start;
    
    // If no change needed, set immediately
    if (range === 0) {
        element.textContent = isFloat ? end.toFixed(1) : Math.round(end);
        return;
    }
    
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        
        element.textContent = isFloat ? current.toFixed(1) : Math.round(current);
    }, 16);
}

// Format duration in minutes to readable format
function formatDuration(minutes) {
    if (minutes < 60) {
        return `${minutes} min`;
    }
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (mins === 0) {
        return `${hours}h`;
    }
    
    return `${hours}h ${mins}m`;
}

// Show success message
function showSuccess(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-weight: 600;
    `;
    toast.textContent = message;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Show error message
function showError(message) {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-weight: 600;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

