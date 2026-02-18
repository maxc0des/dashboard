import os
import time
import requests
from io import BytesIO
from PIL import Image, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106  # Wichtig: sh1106 statt ssd1306
from luma.core.render import canvas
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# 1. Setup & Pfade
load_dotenv()
serial = i2c(port=1, address=0x3C)
device = sh1106(serial) # Dein Display
cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache")

# 2. Spotify API Setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-read-currently-playing",
    open_browser=False, # Für Headless Pi
    cache_path=cache_path
))

# Globale Variablen für flüssiges Scrolling
scroll_pos = 0

def get_album_art(url):
    """Lädt Cover, skaliert es und dithered es für das OLED."""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("L") # Graustufen
        img = img.resize((62, 62)) # Quadratisch für die linke Seite
        return img.convert("1") # 1-Bit Schwarz/Weiß mit Dithering
    except:
        return None

def draw_display(data):
    global scroll_pos
    with canvas(device) as draw:
        if not data:
            draw.text((20, 25), "Spotify Pause", fill="white")
            return

        # --- Linke Seite: Cover ---
        if 'cover_img' in data:
            draw.bitmap((0, 0), data['cover_img'], fill="white")

        # --- Rechte Seite: Infos (ab x=66) ---
        x_text = 66
        max_w = 128 - x_text

        # Titel (Scrollend falls zu lang)
        title = data['title']
        w_title = draw.textlength(title)
        if w_title > max_w:
            x_scroll = x_text - (scroll_pos % int(w_title + 20))
            draw.text((x_scroll, 2), title, fill="white")
            draw.text((x_scroll + w_title + 20, 2), title, fill="white")
            scroll_pos += 2 # Geschwindigkeit des Scrollens
        else:
            draw.text((x_text, 2), title, fill="white")

        # Interpret (einfach gekürzt)
        draw.text((x_text, 16), data['artist'][:12], fill="white")

        # --- Unten Rechts: Progress Bar ---
        bar_x, bar_y = x_text, 45
        bar_w, bar_h = 58, 5
        elapsed = (time.time() - data['local_ts']) * 1000
        curr_ms = min(data['progress_ms'] + elapsed, data['duration_ms'])
        
        # Rahmen & Füllung
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), outline="white")
        fill_w = int((curr_ms / data['duration_ms']) * bar_w)
        draw.rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), fill="white")

# --- Haupt-Loop ---
current_data = None
last_sync = 0
last_track_id = None

try:
    while True:
        # Alle 15 Sek oder bei Songwechsel syncen
        if time.time() - last_sync > 15:
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
            except Exception as e:
                print(f"Sync Error: {e}")

        draw_display(current_data)
        time.sleep(0.05) # ~20 FPS

except KeyboardInterrupt:
    print("Beendet.")