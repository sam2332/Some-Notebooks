import os
from dotenv import load_dotenv

import PySimpleGUI as sg
import os


def set_key(env_file, key, value):
    """Set or update a key-value pair in a .env file, creating the file if it doesn't exist."""
    if not os.path.exists(env_file):
        # If the file does not exist, create it and write the key-value pair
        with open(env_file, "w") as file:
            file.write(f"{key}={value}\n")
    else:
        # If the file exists, read the existing content
        with open(env_file, "r") as file:
            lines = file.readlines()

        # Remove any existing line with the specified key
        lines = [line for line in lines if not line.startswith(key + "=")]
        # Add the new key-value pair
        lines.append(f"{key}={value}\n")

        # Write the updated content back to the file
        with open(env_file, "w") as file:
            file.writelines(lines)


def check_openai_key():
    # Load .env file if it exists
    if os.path.exists(".env"):
        load_dotenv(".env")

    # Check if OPENAI_KEY is set
    if os.getenv("OPENAI_KEY") is None:
        # Create a GUI form to request the user's OpenAI key
        layout = [
            [sg.Text("Please enter your OpenAI key")],
            [sg.InputText(key="openai_key")],
            [sg.Submit(), sg.Cancel()],
        ]
        window = sg.Window("OpenAI Key Request", layout)

        while True:
            event, values = window.read()
            if event == sg.WINDOW_CLOSED or event == "Cancel":
                break
            if event == "Submit":
                # Save the key into the .env file in pydotenv format
                set_key(".env", "OPENAI_KEY", values["openai_key"])
                break

        window.close()
