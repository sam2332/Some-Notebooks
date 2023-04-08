from flask import Flask, render_template, request, jsonify
import openai
import uuid
import keyring
import jsonpickle
from pathlib import Path
save_location = Path("DB.JsonPickle")
def save_chat_rooms(chatrooms):
    save_location.write_text(jsonpickle.encode(chatrooms))
    
def load_chat_rooms():
    if save_location.exists() == False: return {}
    return jsonpickle.decode(save_location.read_text())
    
    
# Create a Flask application
app = Flask(__name__)
openai.api_key = keyring.get_password("system", "openai_key")

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
    room_name = request.form.get('room_name').capitalize()
    if room_name not in chat_rooms:
        chat_rooms[room_name] = []
        save_chat_rooms(chat_rooms)
        return jsonify({'success': True, 'message': 'Chat room created.'})
    else:
        return jsonify({'success': False, 'message': 'Chat room already exists.'})

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
            messages=[{"role": "user", "content": user_input}]
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


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
