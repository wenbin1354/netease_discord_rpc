import pystray
import os
import sys
import threading
import time
import pypresence
import keyboard
from PIL import Image
from io import BytesIO
import requests
from netease import get_netease_title
from config import COOKIES  # Import cookies from config.py

exit_event = threading.Event()
is_connect = False

client_id = "1205202515180781568"
RPC = pypresence.Presence(client_id)

def on_exit(icon, item):
    exit_event.set()

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):  # When using PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    else:  # When running the script in the development environment
        return os.path.join(os.path.dirname(__file__), relative_path)

def fetch_image_from_url(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    return image

def get_icon_image():
    # URL of the default icon
    icon_url = "https://upload.wikimedia.org/wikipedia/en/7/72/NetEase_Music_icon.png"
    return fetch_image_from_url(icon_url)

menu = (pystray.MenuItem("Exit", on_exit),)
icon_image = get_icon_image()  # Fetch and open the image from the URL
icon = pystray.Icon("discord_netease_rpc", icon_image, "Netease Music RPC", menu)

def fetch_song_cover(song_name, artist_name):
    search_url = "http://music.163.com/api/search/pc"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "s": song_name + " " + artist_name,
        "offset": 0,
        "limit": 1,
        "type": 1  # Type 1 for songs
    }
    
    response = requests.post(search_url, headers=headers, data=data, cookies=COOKIES)
    
    if response.status_code == 200:
        data = response.json()
        if data['result']['songs']:
            song_info = data['result']['songs'][0]
            cover_url = song_info['album']['picUrl']
            return cover_url
    return None

# Thread to run the icon
def thread_icon():
    icon.run()

# Thread to connect to Discord
def thread_connect(exit_event):
    global is_connect

    print("Connecting...")

    while not exit_event.is_set():
        if is_connect:
            time.sleep(0.2)
            continue

        try:
            RPC.connect()
            time.sleep(0.2)
            is_connect = True
            print("Connected")
        except pypresence.exceptions.DiscordNotFound:
            time.sleep(0.2)

# Thread to update RPC
def thread_rpc(exit_event):
    global is_connect

    now_playing = ""
    start_time = 0

    while not exit_event.is_set():
        if not is_connect:
            time.sleep(0.2)
            continue

        title = get_netease_title()
        if not title or now_playing == title:
            time.sleep(0.2)
            continue

        now_playing = title
        start_time = int(time.time())

        # Note: Netease Music default title format is %songname% - %artist%
        name, author = title.split(" - ")
        print(f"Playing: {name} - {author}")

        cover_url = fetch_song_cover(name, author)
        if not cover_url:
            cover_url = "netease"  # Fallback image URL or identifier

        try:
            # Use the fetched cover URL directly
            RPC.update(state=f'Author: {author}', details=f'Playing: {name}', large_image=cover_url, start=start_time)
        except (pypresence.exceptions.PipeClosed, pypresence.exceptions.ConnectionTimeout) as e:
            print(f'Error: {e}')
            print("Disconnected...Trying to reconnect...")
            RPC.close()
            is_connect = False
            start_time = 0
            now_playing = ""

        time.sleep(0.2)

    if is_connect:
        RPC.clear()
        RPC.close()

    icon.stop()

# Thread to listen for exit key press
def listen_for_exit():
    # keyboard.wait('q')
    exit_event.set()

if __name__ == "__main__":
    thread_a = threading.Thread(target=thread_icon)
    thread_b = threading.Thread(target=lambda: thread_connect(exit_event))
    thread_c = threading.Thread(target=lambda: thread_rpc(exit_event))
    thread_d = threading.Thread(target=listen_for_exit)  # Thread for listening to 'q' key press

    thread_a.start()
    thread_b.start()
    thread_c.start()
    thread_d.start()

    thread_a.join()
