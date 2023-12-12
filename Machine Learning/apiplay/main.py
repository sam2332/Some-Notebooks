from Libs.OpenAi import check_openai_key

check_openai_key()

import PySimpleGUI as sg
import sys
import os
from dotenv import load_dotenv, set_key

from Libs.FunctionBot import GPTtoolCaller
from contextlib import redirect_stdout

gpt_caller = GPTtoolCaller(
    system_msg="""try and automate some of the work.
Talk to yourself concisely between tool calls. this is your memory.
do not write messages to the user, they will never see it.
use the tools in the way they were intended
Next message is the instruction to follow.
"""
)


from Command_Library.Memory import setup as memory_setup

memory_setup(gpt_caller)

from Command_Library.FileIO import setup as fileio_setup

fileio_setup(gpt_caller)

from Command_Library.ShellCmd import setup as shellcmd_setup

shellcmd_setup(gpt_caller)

import pickle
import os


class ChatGUI:
    def __init__(self):
        layout = [
            [sg.Text("Chat Log:")],
            [
                sg.Multiline(
                    size=(60, 20),
                    key="log",
                    autoscroll=True,
                    reroute_stdout=True,
                    write_only=True,
                    reroute_cprint=True,
                    expand_x=True,
                    expand_y=True,
                )
            ],
            [
                sg.Multiline(
                    size=(50, 1), key="user_input", expand_x=True, expand_y=False
                ),
                sg.Button("Send", key="Send"),
                sg.Button("Clear", key="Clear"),
            ],
        ]
        self.window = sg.Window(
            "Automaton",
            layout,
            finalize=True,
            resizable=True,
            return_keyboard_events=True,
            use_default_focus=False,
            element_justification="c",
        )
        self.window["user_input"].expand(True, True, True)
        self.window["Send"].expand(False, False, False)
        self.window["Clear"].expand(False, False, False)
        self.window["log"].expand(True, True, True)
        self.history_file = "history.pkl"
        self.load_history()
        self.window["user_input"].SetFocus()
        self.window["user_input"].bind(
            "<Return>", "Send"
        )  # Bind the Enter key to the 'Send' button

    def load_history(self):
        try:
            with open(self.history_file, "rb") as f:
                history = pickle.load(f)
                self.window["log"].update(history)
        except FileNotFoundError:
            pass

    def save_history(self):
        with open(self.history_file, "wb") as f:
            pickle.dump(self.window["log"].get(), f)

    def clear_history(self):
        self.window["log"].update("")
        if os.path.exists(self.history_file):
            os.remove(self.history_file)

    def close(self):
        self.save_history()
        self.window.close()

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            user_input = values["user_input"]
            if (event == "Send" or event == "user_input") and values[
                "user_input"
            ] != "":
                with redirect_stdout(self.window["log"]):
                    print(f"User: {user_input}")
                    gpt_caller.reset()
                    gpt_caller.query(user_input)
                self.save_history()
            elif event == "Clear":
                self.clear_history()
            self.window["user_input"].SetFocus()


gui = ChatGUI()
gui.run()
