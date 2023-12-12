import tempfile
import subprocess


import PySimpleGUI as sg


def show_command_and_get_response(command):
    # Define the window's contents (layout)
    layout = [
        [sg.Text("Command:")],
        [sg.Multiline(command, key="-COMMAND-")],
        [sg.Button("Accept"), sg.Button("Reject")],
    ]

    # Create the window
    window = sg.Window("Command Confirmation", layout)

    # Event loop to process "events"
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Reject":
            response = False
            break
        if event == "Accept":
            response = True
            break

    # Close the window
    window.close()
    return response


def setup(gpt_caller):
    @gpt_caller.register_tool
    def run_bash_command(command):
        """Runs command in bash profile of logged in user"""
        if show_command_and_get_response(command):
            return subprocess.check_output(command, shell=True).decode("utf-8")
        else:
            return "bash command rejected by user, please stop and wait for directions."

    @gpt_caller.register_tool
    def run_python_command(code):
        """Execute a python code file using subprocess and temp file"""
        if show_command_and_get_response(code):
            with tempfile.NamedTemporaryFile(suffix=".py") as temp:
                temp.write(code.encode("utf-8"))
                temp.flush()
                return subprocess.check_output(["python", temp.name]).decode("utf-8")
        else:
            return "python command rejected by user, please stop and wait for directions."
