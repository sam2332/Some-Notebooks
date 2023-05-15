import webview
import keyboard
import threading

def create_webview():
    url = 'https://it15536:5002/'
    webview.create_window('My WebView', url, fullscreen=False)
    webview.start()

def check_hotkey():
    while True:
        if keyboard.is_pressed('ctrl+insert'):
            keyboard_thread = threading.Thread(target=create_webview)
            keyboard_thread.daemon = True
            keyboard_thread.start()
if __name__ == '__main__':
    check_hotkey()