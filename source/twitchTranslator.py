import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os
import webbrowser
import socket
import requests
import time
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from googletrans import Translator
import sys

# Global variables
translator = Translator()
access_token = None
message_history = {}
chat_socket = None

# Configuration variables
client_id = None
client_secret = None
redirect_uri = None
target_username = None
target_language = None

def get_config_path():
    """Returns the path to the config file in a user-writable location."""
    base_dir = os.path.expanduser("~")
    config_dir = os.path.join(base_dir, ".twitch_translator")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.txt")

def load_config():
    global client_id, client_secret, redirect_uri, target_username, target_language

    try:
        if getattr(sys, 'frozen', False):
            script_dir = sys._MEIPASS
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        config_file_path = os.path.join(script_dir, 'config.txt')

        if not os.path.exists(config_file_path):
            raise FileNotFoundError("Config file not found.")

        with open(config_file_path, 'r') as config_file:
            lines = config_file.readlines()

        client_id = lines[5].strip() if len(lines) > 5 else None
        client_secret = lines[9].strip() if len(lines) > 9 else None
        redirect_uri = lines[13].strip() if len(lines) > 13 else None
        target_channel_url = lines[17].strip() if len(lines) > 17 else None
        target_username = target_channel_url.split("/")[-1] if target_channel_url else None
        target_language = lines[21].strip() if len(lines) > 21 else None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load configuration: {e}")

def open_config():
    """Opens the config file in Notepad (Windows) or a text editor."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write("# Configuration file for Twitch Chat Translator\n")
    os.system(f'notepad "{config_path}"')

def get_access_token(auth_code):
    token_url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        messagebox.showerror("Error", f"Failed to get access token: {response.text}")
        return None

class OAuthRedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        if "code" in query:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful. You can close this window.")
            self.server.auth_code = query["code"][0]

    def log_message(self, format, *args):
        return

def get_auth_code_via_redirect():
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, OAuthRedirectHandler)
    httpd.handle_request()
    return getattr(httpd, "auth_code", None)

def connect_to_twitch_chat(channel_name, chat_display):
    global chat_socket
    server = "irc.chat.twitch.tv"
    port = 6667
    nickname = client_id
    oauth_token = f"oauth:{access_token}"
    channel = f"#{channel_name}"

    chat_socket = socket.socket()
    chat_socket.connect((server, port))
    chat_socket.send(f"PASS {oauth_token}\n".encode("utf-8"))
    chat_socket.send(f"NICK {nickname}\n".encode("utf-8"))
    chat_socket.send(f"JOIN {channel}\n".encode("utf-8"))

    chat_display.config(state='normal')
    chat_display.insert(tk.END, f"Connected to chat for channel: {channel_name}\n")
    chat_display.config(state='disabled')

    while True:
        response = chat_socket.recv(2048).decode("utf-8")
        if response.startswith("PING"):
            chat_socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        elif len(response) > 0:
            parse_and_display_chat(response, chat_display)

def parse_and_display_chat(response, chat_display):
    if "PRIVMSG" in response:
        parts = response.split(":", 2)
        if len(parts) >= 3:
            username = parts[1].split("!", 1)[0]
            message = parts[2].strip()
            current_time = time.strftime("%H:%M:%S")

            detected_language = translator.detect(message).lang
            print(detected_language)
            if detected_language != target_language:
                translated_message = translator.translate(message, src=detected_language, dest=target_language).text
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"[{current_time}] {username}: {message} ", "default")
                chat_display.insert(tk.END, f"[{detected_language}] {translated_message}\n", "translated")
                chat_display.config(state='disabled')
            else:
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"[{current_time}] {username}: {message}\n", "default")
                chat_display.config(state='disabled')
            chat_display.yview(tk.END)

def main_gui():
    def open_config():
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
        os.startfile(config_path)

    def start_bot():
        load_config()
        if not (client_id and client_secret and redirect_uri and target_username and target_language):
            messagebox.showerror("Error", "Please ensure all configuration fields are filled in.")
            return

        auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=chat:read"
        webbrowser.open(auth_url)

        auth_code = get_auth_code_via_redirect()
        if auth_code:
            global access_token
            access_token = get_access_token(auth_code)
            if access_token:
                switch_to_chat_page()
            else:
                messagebox.showerror("Error", "Failed to retrieve access token.")

    def switch_to_chat_page():
        root.destroy()
        chat_page()

    root = tk.Tk()
    root.title("Twitch Chat Translator")

    main_frame = tk.Frame(root)
    main_frame.pack(padx=10, pady=10)

    tk.Button(main_frame, text="Open Config", command=open_config, width=20).pack(pady=5)
    tk.Button(main_frame, text="Start", command=start_bot, width=20).pack(pady=5)

    root.mainloop()

def chat_page():
    def back_to_main_menu():
        chat_root.destroy()
        main_gui()

    chat_root = tk.Tk()
    chat_root.title("Twitch Chat Translator - Chat View")

    chat_display = scrolledtext.ScrolledText(chat_root, wrap=tk.WORD, height=20, width=80, state='disabled')
    chat_display.pack(pady=10)

    chat_display.tag_configure("default", foreground="black")
    chat_display.tag_configure("translated", foreground="red")

    button_frame = tk.Frame(chat_root)
    button_frame.pack(pady=5)

    tk.Button(button_frame, text="Exit", command=chat_root.quit, width=20).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Main Menu", command=back_to_main_menu, width=20).pack(side=tk.LEFT, padx=5)

    threading.Thread(target=connect_to_twitch_chat, args=(target_username, chat_display), daemon=True).start()

    chat_root.mainloop()

if __name__ == "__main__":
    main_gui()