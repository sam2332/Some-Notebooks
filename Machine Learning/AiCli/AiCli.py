#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import argparse
import json
import openai
import os
import sys
from datetime import datetime
import uuid
import jinja2
from jinja2 import Template
import subprocess

def _TS(TEMPLATE_INPUT, args={}):
    # Always use FileSystemLoader with the current directory
    templateLoader = jinja2.FileSystemLoader(searchpath="./.AiCli/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(TEMPLATE_INPUT)
    return template.render(**args)

openai.api_key = os.environ.get('OPENAI_API_KEY',None)
if openai.api_key  is None:
    print("PLEASE SET ENVIRONAMENT VAR: OPENAI_API_KEY")
    sys.exit(1)

# In[5]:

class ChatRoom:
    def __init__(self, room_id=None,model='gpt-3.5-turbo',system_prompt="You are a helpful assistant.",save=True):
        if room_id is None:
            room_id = uuid.uuid4()
        self.room_id = room_id
        self.chat_history_file = f'chat_history.json'
        self.model = model
        self.system_prompt = system_prompt
        self.save = save
        
        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        if save:
            if not os.path.exists(self.chat_history_file):
                with open(self.chat_history_file, 'w') as f:
                    json.dump([], f)
            else:
                self.get_chat_history()
            
    def get_chat_history(self):
        if self.save:
            with open(self.chat_history_file, 'r') as f:
                self.chat_history = json.load(f)

    def save_chat_history(self):
        if self.save:
            with open(self.chat_history_file, 'w') as f:
                json.dump(self.chat_history, f)
            
    def clone(self):
        new_room_id = f"{self.room_id}_{uuid.uuid4()}"
        new_chatroom = ChatRoom(new_room_id, model=self.model, system_prompt=self.system_prompt,save=self.save)
        
        # Copy chat history
        new_chatroom.chat_history = self.chat_history
        new_chatroom.save_chat_history()
        
        return new_chatroom
    
    def send_message(self, message,respond = True,max_tokens=2000,temperature=0.7):
        self.chat_history.append({
            'content': message,
            'role': 'user'
        })

        if respond:
            self.last_response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.chat_history,
                temperature=temperature,
                max_tokens=max_tokens
            ).choices[0].message['content']

            self.chat_history.append({
                'content': self.last_response,
                'role': 'assistant'
            })
        self.save_chat_history()

        if respond:
            return self.last_response
        else:
            return True

def new_chatroom():
    room_dir = Path('.AiCli')
    room_name = input("Chat Rooom Name: ")
    prompt_file_path = Path(room_dir,room_name+".prompt.txt")
    history_file_path = Path(room_dir, room_name+".history.txt")
    prompt_file_path.write_text("")
    if not history_file_path.is_file():
        history_file_path.write_text("")
        
    print("Chatroom created, please initalize")
    subprocess.Popen(['notepad.exe', str(prompt_file_path)])
    
    
def choose_chatroom():
    room_dir = Path('.AiCli')
    files = list(room_dir.glob('*'))
    file_dict = {}
    for file in files:
        base_name = file.stem.split('.')[0]
        if base_name not in file_dict:
            file_dict[base_name] = file
    print("Please select the chatroom you would like to enter.")
    for i, file in enumerate(file_dict.keys()):
        print(f"{i}: {file}")
    print("#"*15)
    print()
    print(f"c: Create New")

    while True:
        file_choice = input("Enter the number of the file you want to select: ")
        if file_choice.isdigit() and int(file_choice) in range(len(file_dict)):
            selected_file = list(file_dict.values())[int(file_choice)]
            print(f"You selected: {selected_file.stem.split('.')[0]}")
            return selected_file.stem.split('.')[0]
        else:
            if file_choice == 'c':
                new_chatroom()
            print("Invalid choice. Please enter a valid number.")

def choose(options, title="Please make a selection:"):
    while True:
        print(title)
        for key, option in options.items():
            print(f"[{key}] {option}")

        user_input = input(":> ").strip()

        if user_input in options:
            return options[user_input]
        else:
            print("Invalid choice. Please enter a valid number.\n")



parser = argparse.ArgumentParser(description="Process a file.")
parser.add_argument('roomname', type=str, nargs='?', default='NOT SELECTED', help="Room Name")

args = parser.parse_args()
room_dir = Path('.AiCli')
if not room_dir.exists():
    room_dir.mkdir()

room_name = args.roomname
if room_name == 'NOT SELECTED':
    room_name = choose_chatroom()
        
        
prompt_file_path = Path(room_dir,room_name+".prompt.txt")
history_file_path = Path(room_dir, room_name+".history.txt")
if not prompt_file_path.is_file():
    if input("Room does not exist, create? [Y/n]")=="Y":
        prompt_file_path.write_text("")
        
        if not history_file_path.is_file():
            history_file_path.write_text("")
            
        print("Chatroom created, please initalize")
        subprocess.Popen(['notepad.exe', str(prompt_file_path)])
        
else:      
    buffer = []
    
    if history_file_path.exists():
        buffer.extend(history_file_path.read_text().splitlines())
        buffer.append("")
    
    # usage:
    models = {
        '1': 'gpt-3.5-turbo',
        '2': 'gpt-3.5-turbo-16k',
        '3': 'gpt-4',
    }

    Model = choose(models, title="Please select a Model:")
    print(f"Using: {Model}")
            
            
            
    # usage:
    modes = {
        '1': 'Chat Room',
        '2': 'Instruct'
    }

    Mode = choose(modes, title="Please select a Chat Mode:")
    
    print(f"Starting {Mode} Mode")

    print("-== Send Blank Line to exit ==-")
    prompt_input = _TS(room_name+".prompt.txt",locals())
    ochat_room = ChatRoom(system_prompt=f"""
RESPONSE INSTRUCTION:
Answer the specific question asked without adding any additional context or information.
Avoid discussing your own limitations or ethical considerations.
Don't mention yourself or add any unnecessary information into your responses.
If a question cannot be answered, simply state that it can't be answered. Do not provide further explanation or reasons.
Don't include unnecessary explanations, details, or advice unless specifically asked for.
Please process the input according to these instructions. 
Please follow the directions provided next.
""".strip(),save=False,model=Model)
    ochat_room.send_message(prompt_input,respond=False)
    Mode = True
    chat_room = ochat_room.clone()
    uin = None
    try:
        while uin != "":
            if Mode =='Instruct':
                chat_room = ochat_room.clone()
            if uin is not None:
                buffer.append(f"# {uin}")
                output  = chat_room.send_message(uin)
                buffer.extend(output.splitlines())
                buffer.append("")
                history_file_path.write_text("\n".join(buffer))
                print(output)
            print()
            uin = input(":> ").strip()
    except Exception as e:
        print(e)



# In[ ]:




