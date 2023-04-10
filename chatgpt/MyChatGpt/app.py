from flask import Flask, render_template, request, jsonify
import openai
import uuid
import keyring
import jsonpickle
import os
from pathlib import Path

save_location = Path("DB.JsonPickle")


def save_topic_rooms(topicrooms):
    save_location.write_text(jsonpickle.encode(topicrooms))


def load_topic_rooms():
    if save_location.exists() == False:
        return {}
    return jsonpickle.decode(save_location.read_text())


def convertMessagesToGPTFormat(a):
    msg = []
    for item in a:
        if "user" in item:
            msg.append({"role": "user", "content": item["user"]})
        if "gpt" in item:
            msg.append({"role": "assistant", "content": item["gpt"]})
        if "system" in item:
            msg.append({"role": "system", "content": item["system"]})
    return msg


import locale


def format_currency(value):
    # Set the locale to use the appropriate formatting for currency
    locale.setlocale(locale.LC_MONETARY, "en_US.UTF-8")

    # Format the value as currency
    formatted_currency = locale.currency(value, symbol="$", grouping=True)
    return formatted_currency


# Create a Flask application
app = Flask(__name__)
openai.api_key = keyring.get_password("system", "openai_key")

# Specify the path to the folder you want to read
system_templates_folder_path = "SystemTemplates"
archive_folder_path = "Archives"

# Initialize Topics dictionary
topic_rooms = load_topic_rooms()


@app.route("/get_topic_names", methods=["GET"])
def get_topic_names():
    topic_names = list(topic_rooms.keys())
    return jsonify({"success": True, "topic_names": topic_names})


# Route for the home page to create or join Topics
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_billing_total", methods=["GET"])
def get_billing_total():
    room_name = request.args.get("room_name")


    if room_name in topic_rooms:
    
        return jsonify({
            "success": True,
            "billing_total": str(topic_rooms[room_name]["meta"]["tokens_spent"])+ " tokens or "+format_currency(
                (float(topic_rooms[room_name]["meta"]["tokens_spent"])/1000)*float(0.002)
            ),
        })
    else:
        return jsonify({"success": False, "message": "Topic not found."})
    


@app.route("/get_topic_info", methods=["GET"])
def get_topic_info():
    room_name = request.args.get("room_name")
    if room_name in topic_rooms:
        return jsonify({"success": True, "topic_history": topic_rooms[room_name]})
    else:
        return jsonify({"success": False, "message": "Topic not found."})


# Route to create a new Topic
@app.route("/create_topic", methods=["POST"])
def create_topic():
    global token_running_total, token_running_total_location
    room_name = request.form.get("room_name")
    roomSystemMsg = request.form.get("roomSystemMsg")
    if room_name not in topic_rooms:
        if roomSystemMsg == "":
            topic_rooms[room_name] = {"messages": [], "meta": {"tokens_spent": 0}}
        else:
            system_id = str(uuid.uuid4())
            topic_rooms[room_name] = {}
            topic_rooms[room_name]["messages"] = [
                {"id": system_id, "system": roomSystemMsg}
            ]
            topic_rooms[room_name]["meta"] = {"tokens_spent": 0}
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=convertMessagesToGPTFormat(
                    topic_rooms[room_name]["messages"]
                ),  # [{"role": "user", "content": user_input}]
            )
            gpt_response = response["choices"][0]["message"]["content"]
            response_id = str(uuid.uuid4())
            topic_rooms[room_name]["messages"].append(
                {"id": response_id, "gpt": gpt_response}
            )
            topic_rooms[room_name]["meta"]["tokens_spent"] += response["usage"][
                "total_tokens"
            ]
        save_topic_rooms(topic_rooms)
        return jsonify({"success": True, "message": "Topic created."})
    else:
        return jsonify({"success": False, "message": "Topic already exists."})


# Route to delete a Topic
@app.route("/delete_topic", methods=["POST"])
def delete_topic():
    room_name = request.form.get("room_name")
    if room_name in topic_rooms:
        del topic_rooms[room_name]
        save_topic_rooms(topic_rooms)
        return jsonify({"success": True, "message": "Topic deleted."})
    else:
        return jsonify({"success": False, "message": "Topic not found."})


@app.route("/get_folder_contents")
def get_folder_contents():
    try:
        # List all files in the specified folder
        filenames = [
            f
            for f in os.listdir(system_templates_folder_path)
            if os.path.isfile(os.path.join(system_templates_folder_path, f))
        ]
        return jsonify({"success": True, "folder_contents": filenames})
    except Exception as e:
        # Handle exceptions (e.g., folder not found)
        return jsonify({"success": False, "message": str(e)})


@app.route("/get_file_content")
def get_file_content():
    try:
        # Get the filename from the query parameter
        filename = request.args.get("filename")

        # Validate the filename
        if not filename:
            return jsonify({"success": False, "message": "Filename is required."})

        # Construct the full file path
        file_path = os.path.join(system_templates_folder_path, filename)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return jsonify({"success": False, "message": f"File not found: {filename}"})

        # Read the content of the file
        with open(file_path, "r") as file:
            file_content = file.read()

        return jsonify({"success": True, "file_content": file_content})
    except Exception as e:
        # Handle exceptions (e.g., file read error)
        return jsonify({"success": False, "message": str(e)})


@app.route("/rename_topic_room", methods=["POST"])
def rename_topic_room():
    current_room_name = request.form.get("current_room_name")
    new_room_name = request.form.get("new_room_name")
    # Check if the current room exists and the new room name is not empty
    if current_room_name in topic_rooms and new_room_name:
        # Check if the new room name already exists
        if new_room_name in topic_rooms:
            return jsonify(
                {"success": False, "message": "The new Topic name already exists."}
            )

        # Rename the Topic by reassigning the topic history
        topic_rooms[new_room_name] = topic_rooms[current_room_name]
        del topic_rooms[current_room_name]
        save_topic_rooms(topic_rooms)

        return jsonify({"success": True, "message": "Topic renamed successfully."})
    else:
        return jsonify(
            {"success": False, "message": "Topic not found or new room name is empty."}
        )


# Route to handle topic input from the user and generate GPT-4 response
@app.route("/send_message", methods=["POST"])
def send_message():
    global token_running_total, token_running_total_location
    room_name = request.form.get("room_name")
    user_input = request.form.get("user_input")
    message_id = str(uuid.uuid4())
    if room_name in topic_rooms:
        topic_rooms[room_name]["messages"].append(
            {"id": message_id, "user": user_input}
        )

        # Call the GPT-4 API to generate a response (Note: Adjust this for GPT-4 specifications)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=convertMessagesToGPTFormat(
                topic_rooms[room_name]["messages"]
            ),  # [{"role": "user", "content": user_input}]
        )
        gpt_response = response["choices"][0]["message"]["content"]
        response_id = str(uuid.uuid4())
        topic_rooms[room_name]["messages"].append(
            {"id": response_id, "gpt": gpt_response}
        )
        topic_rooms[room_name]["meta"]["tokens_spent"] += response["usage"][
            "total_tokens"
        ]
        save_topic_rooms(topic_rooms)
        return jsonify(
            {
                "success": True,
                "gpt_response": gpt_response,
                "message_id": message_id,
                "response_id": response_id,
            }
        )
    else:
        return jsonify({"success": False, "message": "Topic not found."})


# Route to delete a specific message from a Topic
@app.route("/delete_message", methods=["POST"])
def delete_message():
    room_name = request.form.get("room_name")
    message_id = request.form.get("message_id")
    if room_name in topic_rooms:
        topic_rooms[room_name]["messages"] = [
            msg for msg in topic_rooms[room_name]["messages"] if msg["id"] != message_id
        ]
        save_topic_rooms(topic_rooms)
        return jsonify({"success": True, "message": "Message deleted."})
    else:
        return jsonify({"success": False, "message": "Topic not found."})


@app.route("/archive_topics", methods=["POST"])
def archive_topics():
    folder_path = request.form.get("folder_path")
    room_name = request.form.get("room_name")  # The Topic to archive

    if not folder_path:
        return jsonify({"success": False, "message": "Folder path is required."})
    if not room_name:
        return jsonify({"success": False, "message": "Topic name is required."})

    # Create the folder if it does not exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Generate a filename based on the current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"topic_archive_{room_name}_{timestamp}.txt"
    file_path = os.path.join(archive_folder, folder_path, filename)

    # Get the topic history from topic_rooms
    topic_history = topic_rooms.get(room_name, {"messages": []})
    if not topic_history:
        return jsonify(
            {
                "success": False,
                "message": f"No topic history found for room: {room_name}",
            }
        )

    # Save the topic history to the file
    with open(file_path, "w") as file:
        for message in topic_history:
            file.write(message + "\n")

    return jsonify(
        {"success": True, "message": f"Chat history archived to: {file_path}"}
    )


# Run the Flask application
if __name__ == "__main__":
    import random, threading, webbrowser

    port = 5002
    url = "http://127.0.0.1:{0}".format(port)

    threading.Timer(1.25, lambda: webbrowser.open(url) ).start()

    app.run(debug=True,port=port)
