import os
import time
import requests
from io import BytesIO
from PIL import Image, ImageFont
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def init_spotify():
    load_dotenv()
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="user-read-currently-playing",
        open_browser=False, # Für Headless Pi
        cache_path=cache_path
    ))

    current_data = None
    last_sync = 0
    last_track_id = None
    predicted_end = 0

    return sp, current_data, last_sync, last_track_id, predicted_end

def get_album_art(url):
    """Lädt Cover, skaliert es und dithered es für das OLED."""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("L") # Graustufen
        img = img.resize((62, 62)) # Quadratisch für die linke Seite
        return img.convert("1") # 1-Bit Schwarz/Weiß mit Dithering
    except:
        return None

def update_spotify(sp, current_data, last_sync, last_track_id):

    try:
        track = sp.currently_playing()
        if track and track['is_playing']:
            t_id = track['item']['id']
            if t_id != last_track_id:
                # Neuer Song! Cover laden
                img_url = track['item']['album']['images'][0]['url']
                cover = get_album_art(img_url)
                last_track_id = t_id
            else:
                cover = current_data['cover_img'] if current_data else None

            current_data = {
                'title': track['item']['name'],
                'artist': track['item']['artists'][0]['name'],
                'progress_ms': track['progress_ms'],
                'duration_ms': track['item']['duration_ms'],
                'local_ts': time.time(),
                'cover_img': cover
            }
        else:
            current_data = None
        last_sync = time.time()
        predicted_end = time.time() + (current_data['duration_ms'] - current_data['progress_ms']) / 1000 if current_data else None
    except Exception as e:
        print(f"Sync Error: {e}")

    return current_data, last_sync, last_track_id, predicted_end