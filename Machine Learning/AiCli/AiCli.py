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

def _TS(TEMPLATE_INPUT, args={}):
    # Always use FileSystemLoader with the current directory
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    
    # Check if the input is a file in the current directory
    if os.path.isfile(TEMPLATE_INPUT):
        # Load from a file
        template = templateEnv.get_template(TEMPLATE_INPUT)
    else:
        # If not a file, load from a string
        # However, the FileSystemLoader is still in effect for any imported/included templates
        template = Template(TEMPLATE_INPUT)
        template.environment = templateEnv

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
    
    def send_message(self, message,respond = True,max_tokens=700,temperature=0.7):
        self.chat_history.append({
            'content': message,
            'role': 'user'
        })

        if respond:
            token_count = 0
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
        

parser = argparse.ArgumentParser(description="Process a file.")
parser.add_argument('roomname', type=str, nargs='?', default='default', help="Room Name")

args = parser.parse_args()
prompt_file_path = args.roomname+".chat.prompt"
history_file_path = Path(args.roomname+".chat.history")
if not history_file_path.is_file():
    history_file_path.write_text("")
if not Path(prompt_file_path).is_file():
    if input("Room does not exist, create? [Y/n]")=="Y":
        Path(prompt_file_path).write_text(""" 
        Please Put input content info into this file.    
        """)
        print("Chatroom created, please initalize")
    
else:   
    
    buffer = []
    
    if history_file_path.exists():
        buffer.extend(history_file_path.read_text().splitlines())
        
    ochat_room = ChatRoom(system_prompt=f"""
RESPONSE INSTRUCTION:
Answer the specific question asked without adding any additional context or information.
Avoid discussing your own limitations or ethical considerations.
Don't mention yourself or add any unnecessary information into your responses.
If a question cannot be answered, simply state that it can't be answered. Do not provide further explanation or reasons.
Don't include unnecessary explanations, details, or advice unless specifically asked for.
Please process the input according to these instructions. 
Please follow the directions provided in the input text.

The content of the users directions will be provided in the next message.
    """.strip(),save=False,model='gpt-4')
    
    output = ochat_room.send_message(_TS(prompt_file_path,locals()), respond=input("Generate Inital Response [Y/n]:> ").lower()=="y")
    if not isinstance(output,bool):
        buffer.extend(output.splitlines())
        print(output)
 
    Mode = True
    chat_room = ochat_room.clone()
    
    while True:
        uin = input("[1] Chat Room or [2] Instruct:> ")
        if uin.strip() =='1':
            Mode = 'Chat'
            print("Starting Chat Mode")
            break
        if uin.strip() =='2':
            Mode = 'Instruct'
            print("Starting Instruct Mode")
            break
    print("-== Send Blank Line to exit ==-")
        
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




