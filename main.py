#display
from luma.core.interface.serial import i2c # type: ignore
from luma.oled.device import sh1106 # type: ignore
from luma.core.render import canvas # type: ignore
import time

from spotify import *

widgets = ["spotify", "clock", "status"]
mode = "spotify"
running = True

#threading
import threading

#display setup
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)
scroll_pos = 0

#set up input thread
def input_thread():
    while True:
        user_input = input("Enter command: ")
        if user_input == "exit":
            global running
            running = False
            break
        elif user_input == "":
            print("next")
            global mode
            mode = widgets[(widgets.index(mode) + 1) % len(widgets)]

def draw_display(mode, data):
    global scroll_pos
    with canvas(device) as draw:
        if not data:
            draw.text((20, 25), "Spotify Pause", fill="white")
            return

        if 'cover_img' in data:
            draw.bitmap((0, 0), data['cover_img'], fill="white")

        x_text = 66
        max_w = 128 - x_text

        title = data['title']
        w_title = draw.textlength(title)
        if w_title > max_w:
            x_scroll = x_text - (scroll_pos % int(w_title + 20))
            draw.text((x_scroll, 2), title, fill="white")
            draw.text((x_scroll + w_title + 20, 2), title, fill="white")
            scroll_pos += 2
        else:
            draw.text((x_text, 2), title, fill="white")

        draw.text((x_text, 16), data['artist'][:12], fill="white")

        bar_x, bar_y = x_text, 45
        bar_w, bar_h = 58, 5
        elapsed = (time.time() - data['local_ts']) * 1000
        curr_ms = min(data['progress_ms'] + elapsed, data['duration_ms'])
        
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), outline="white")
        fill_w = int((curr_ms / data['duration_ms']) * bar_w)
        draw.rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), fill="white")


if __name__ == "__main__":
    #intit
    threading.Thread(target=input_thread, daemon=True).start()
    sp, current_data, last_sync, last_track_id, predicted_end = init_spotify()

    #main loop
    while True:
        try:
            if mode == "spotify":
                while running:
                    if time.time() - last_sync > 5 or time.time() > predicted_end:
                        current_data, last_sync, last_track_id, predicted_end = update_spotify(sp, current_data, last_sync, last_track_id)
                    draw_display("spotify", current_data)
                    time.sleep(0.05)
        except KeyboardInterrupt:
            break