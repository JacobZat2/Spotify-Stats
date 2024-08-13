from collections import Counter
import os
from flask import Flask, redirect, request, session, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Set up Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()

# Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Scope for top artists and tracks data
SCOPE = "user-top-read"

# Spotify OAuth object
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, 
                        client_secret=SPOTIPY_CLIENT_SECRET, 
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=SCOPE)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    session['token_info'] = token_info
    return redirect(url_for('top_stats'))

@app.route('/top-stats')
def top_stats():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get user's top artists (limit increased to 12)
    artists_results = sp.current_user_top_artists(limit=12, time_range='medium_term')
    top_artists = artists_results['items']

    # Get user's top tracks (limit increased to 12)
    tracks_results = sp.current_user_top_tracks(limit=12, time_range='medium_term')
    top_tracks = tracks_results['items']

    # Calculate most-listened-to genres for the pie chart
    genres = []
    for artist in top_artists:
        genres.extend(artist['genres'])
    genre_counts = Counter(genres).most_common(5)  # Top 5 genres

    genre_labels = [genre[0] for genre in genre_counts]
    genre_values = [genre[1] for genre in genre_counts]

    # Get recommended artists based on top artists
    seed_artists = [artist['id'] for artist in top_artists[:5]]  # Use up to 5 top artists as seeds
    recommended_artists_results = sp.recommendations(seed_artists=seed_artists, limit=6)
    recommended_artists = recommended_artists_results['tracks']

    return render_template('top_stats.html', 
                           artists=top_artists, 
                           tracks=top_tracks, 
                           genre_labels=genre_labels, 
                           genre_values=genre_values,
                           recommended_artists=recommended_artists)

if __name__ == '__main__':
    app.run(debug=True)
