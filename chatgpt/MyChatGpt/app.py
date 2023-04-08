from flask import Flask, render_template, request, jsonify
import openai
import uuid
import keyring
import jsonpickle
import os
from pathlib import Path
save_location = Path("DB.JsonPickle")
def save_chat_rooms(chatrooms):
    save_location.write_text(jsonpickle.encode(chatrooms))
    
def load_chat_rooms():
    if save_location.exists() == False: return {}
    return jsonpickle.decode(save_location.read_text())
    
def convertMessagesToGPTFormat(a):
    msg = []
    for item in a:
        if'user' in item:
            msg.append({'role':'user','content':item['user']}) 
        if'gpt' in item:
            msg.append({'role':'assistant','content':item['gpt']}) 
        if'system' in item:
            msg.append({'role':'system','content':item['system']}) 
    return msg


# Create a Flask application
app = Flask(__name__)
openai.api_key = keyring.get_password("system", "openai_key")
print(openai.api_key)

# Initialize chat rooms dictionary
chat_rooms = load_chat_rooms()
    
@app.route('/get_chat_names', methods=['GET'])
def get_chat_names():
    chat_names = list(chat_rooms.keys())
    return jsonify({'success': True, 'chat_names': chat_names})

# Route for the home page to create or join chat rooms
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    room_name = request.args.get('room_name')
    if room_name in chat_rooms:
        return jsonify({'success': True, 'chat_history': chat_rooms[room_name]})
    else:
        return jsonify({'success': False, 'message': 'Chat room not found.'})

# Route to create a new chat room
@app.route('/create_chat', methods=['POST'])
def create_chat():
    room_name = request.form.get('room_name')
    roomSystemMsg = request.form.get('roomSystemMsg')
    if room_name not in chat_rooms:
        if roomSystemMsg !="":
            system_id = str(uuid.uuid4())
            chat_rooms[room_name] = [{'id':system_id, 'system':roomSystemMsg}]   

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=convertMessagesToGPTFormat(chat_rooms[room_name])#[{"role": "user", "content": user_input}]
            )
            gpt_response = response['choices'][0]['message']['content']
            response_id = str(uuid.uuid4())
            chat_rooms[room_name].append({'id': response_id, 'gpt': gpt_response})
        save_chat_rooms(chat_rooms)
        return jsonify({'success': True, 'message': 'Chat room created.'})
    else:
        return jsonify({'success': False, 'message': 'Chat room already exists.'})

# Route to delete a chat room
@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    room_name = request.form.get('room_name')
    if room_name in chat_rooms:
        del chat_rooms[room_name]
        save_chat_rooms(chat_rooms)
        return jsonify({'success': True, 'message': 'Chat room deleted.'})
    else:
        return jsonify({'success': False, 'message': 'Chat room not found.'})
# Specify the path to the folder you want to read
system_templates_folder_path = 'SystemTemplates'
archive_folder_path = "Archives"
@app.route('/get_folder_contents')
def get_folder_contents():
    try:
        # List all files in the specified folder
        filenames = [f for f in os.listdir(system_templates_folder_path) if os.path.isfile(os.path.join(system_templates_folder_path, f))]
        return jsonify({'success': True, 'folder_contents': filenames})
    except Exception as e:
        # Handle exceptions (e.g., folder not found)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_file_content')
def get_file_content():
    try:
        # Get the filename from the query parameter
        filename = request.args.get('filename')

        # Validate the filename
        if not filename:
            return jsonify({'success': False, 'message': 'Filename is required.'})

        # Construct the full file path
        file_path = os.path.join(system_templates_folder_path, filename)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return jsonify({'success': False, 'message': f'File not found: {filename}'})

        # Read the content of the file
        with open(file_path, 'r') as file:
            file_content = file.read()

        return jsonify({'success': True, 'file_content': file_content})
    except Exception as e:
        # Handle exceptions (e.g., file read error)
        return jsonify({'success': False, 'message': str(e)})


@app.route('/rename_chat_room', methods=['POST'])
def rename_chat_room():
    current_room_name = request.form.get('current_room_name')
    new_room_name = request.form.get('new_room_name')
    # Check if the current room exists and the new room name is not empty
    if current_room_name in chat_rooms and new_room_name:
        # Check if the new room name already exists
        if new_room_name in chat_rooms:
            return jsonify({'success': False, 'message': 'The new chat room name already exists.'})
        
        # Rename the chat room by reassigning the chat history
        chat_rooms[new_room_name] = chat_rooms[current_room_name]
        del chat_rooms[current_room_name]
        save_chat_rooms(chat_rooms)
        
        return jsonify({'success': True, 'message': 'Chat room renamed successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Chat room not found or new room name is empty.'})



# Route to handle chat input from the user and generate GPT-4 response
@app.route('/chat', methods=['POST'])
def chat():
    room_name = request.form.get('room_name')
    user_input = request.form.get('user_input')
    message_id = str(uuid.uuid4())
    if room_name in chat_rooms:
        chat_rooms[room_name].append({'id': message_id, 'user': user_input})

        # Call the GPT-4 API to generate a response (Note: Adjust this for GPT-4 specifications)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=convertMessagesToGPTFormat(chat_rooms[room_name])#[{"role": "user", "content": user_input}]
        )
        print(response)
        gpt_response = response['choices'][0]['message']['content']
        response_id = str(uuid.uuid4())
        chat_rooms[room_name].append({'id': response_id, 'gpt': gpt_response})
        save_chat_rooms(chat_rooms)
        return jsonify({'success': True, 'gpt_response': gpt_response, 'message_id': message_id, 'response_id': response_id})
    else:
        return jsonify({'success': False, 'message': 'Chat room not found.'})

# Route to delete a specific message from a chat room
@app.route('/delete_message', methods=['POST'])
def delete_message():
    room_name = request.form.get('room_name')
    message_id = request.form.get('message_id')
    if room_name in chat_rooms:
        chat_rooms[room_name] = [msg for msg in chat_rooms[room_name] if msg['id'] != message_id]
        save_chat_rooms(chat_rooms)
        return jsonify({'success': True, 'message': 'Message deleted.'})
    else:
        return jsonify({'success': False, 'message': 'Chat room not found.'})



@app.route('/archive_chats', methods=['POST'])
def archive_chats():
    folder_path = request.form.get('folder_path')
    room_name = request.form.get('room_name')  # The chat room to archive

    if not folder_path:
        return jsonify({'success': False, 'message': 'Folder path is required.'})
    if not room_name:
        return jsonify({'success': False, 'message': 'Chat room name is required.'})

    # Create the folder if it does not exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Generate a filename based on the current date and time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'chat_archive_{room_name}_{timestamp}.txt'
    file_path = os.path.join(archive_folder,folder_path, filename)

    # Get the chat history from chat_rooms
    chat_history = chat_rooms.get(room_name, [])
    if not chat_history:
        return jsonify({'success': False, 'message': f'No chat history found for room: {room_name}'})

    # Save the chat history to the file
    with open(file_path, 'w') as file:
        for message in chat_history:
            file.write(message + '\n')

    return jsonify({'success': True, 'message': f'Chat history archived to: {file_path}'})

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
