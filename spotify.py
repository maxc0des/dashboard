import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

#get vars from .env
load_dotenv()
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

scope = "user-read-currently-playing"

#auth
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))

#get current track
current_track = sp.currently_playing()

if current_track is not None and current_track['is_playing']:
    track_name = current_track['item']['name']
    artist_name = current_track['item']['artists'][0]['name']
    track_length = current_track['item']['duration_ms'] / 1000  # in seconds
    track_progress = current_track['progress_ms'] / 1000  # in seconds
    track_album = current_track['item']['album']['name']
    track_cover = current_track['item']['album']['images'][0]['url']
    track_progress_percent = (track_progress / track_length) * 100
    
else:
    print("Es wird gerade keine Musik abgespielt (oder der Private Modus ist an).")