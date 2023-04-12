from flask import Flask, render_template, request, jsonify
import openai
import uuid
import keyring
import jsonpickle
import os
from pathlib import Path
from flask_cors import CORS


save_location = Path("DB.JsonPickle")


def save_topic_topics(topictopics):
    save_location.write_text(jsonpickle.encode(topictopics))


def load_topic_topics():
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
def convertMessagesToCompletion(a):
    return f"""
        {a[0]['system']}\n\nInput: {a[-1]['user']}\n\nOutput:
    """

def generate_gpt_response(topic_topic):
    model = topic_topic['meta']['model']
    if model  in ["gpt-3.5-turbo"]:
        response =  openai.ChatCompletion.create(
            model=model,
            messages=convertMessagesToGPTFormat(
                topic_topic["messages"]
            ),
        )
        topic_topic["meta"]["tokens_spent"] += response["usage"][
            "total_tokens"
        ]
        return response["choices"][0]["message"]["content"]
    else:
        if len(topic_topic["messages"]) >1: 
            response =  openai.Completion.create(
              model=model,
              prompt=convertMessagesToCompletion(topic_topic["messages"]),
              temperature=1,
              max_tokens=500
            )
            topic_topic["meta"]["tokens_spent"] += response["usage"][
                "total_tokens"
            ]
            return response["choices"][0]["text"]
        return None

import locale


def format_currency(value):
    # Set the locale to use the appropriate formatting for currency
    locale.setlocale(locale.LC_MONETARY, "en_US.UTF-8")

    # Format the value as currency
    formatted_currency = locale.currency(value, symbol="$", grouping=True)
    return formatted_currency


# Create a Flask application
app = Flask(__name__)
CORS(app)
openai.api_key = keyring.get_password("system", "openai_key")

# Specify the path to the folder you want to read
system_templates_folder_path = "SystemTemplates"
archive_folder_path = "Archives"

# Initialize Topics dictionary
topic_topics = load_topic_topics()


@app.route("/get_topic_names", methods=["GET"])
def get_topic_names():
    topic_names = list(topic_topics.keys())
    return jsonify({"success": True, "topic_names": topic_names})


# Route for the home page to create or join Topics
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_billing_total", methods=["GET"])
def get_billing_total():
    topic_name = request.args.get("topic_name")


    if topic_name in topic_topics:
    
        return jsonify({
            "success": True,
            "billing_total": str(topic_topics[topic_name]["meta"]["tokens_spent"])+ " tokens or "+format_currency(
                (float(topic_topics[topic_name]["meta"]["tokens_spent"])/1000)*float(0.002)
            ),
        })
    else:
        return jsonify({"success": False, "message": "Topic not found."})
    


@app.route("/get_topic_info", methods=["GET"])
def get_topic_info():
    topic_name = request.args.get("topic_name")
    if topic_name in topic_topics:
        return jsonify({"success": True, "topic_history": topic_topics[topic_name]})
    else:
        return jsonify({"success": False, "message": "Topic not found."})

# Route to create a new Topic
@app.route("/create_topic", methods=["POST"])
def create_topic():
    global token_running_total, token_running_total_location
    topic_name = request.form.get("topic_name")
    topicSystemMsg = request.form.get("topicSystemMsg")
    modelSelection = request.form.get("modelSelection")
    if topic_name not in topic_topics:
        if topicSystemMsg == "":
            topic_topics[topic_name] = {"messages": [], "meta": {"tokens_spent": 0,"model":modelSelection}}
        else:
            system_id = str(uuid.uuid4())
            topic_topics[topic_name] = {}
            topic_topics[topic_name]["messages"] = [
                {"id": system_id, "system": topicSystemMsg}
            ]
            topic_topics[topic_name]["meta"] = {"tokens_spent": 0,"model":modelSelection}

            gpt_response = generate_gpt_response(topic_topics[topic_name])
            if gpt_response is not None:
                response_id = str(uuid.uuid4())
                topic_topics[topic_name]["messages"].append(
                    {"id": response_id, "gpt": gpt_response}
                )
        save_topic_topics(topic_topics)
        return jsonify({"success": True, "message": "Topic created."})
    else:
        return jsonify({"success": False, "message": "Topic already exists."})


# Route to delete a Topic
@app.route("/delete_topic", methods=["POST"])
def delete_topic():
    topic_name = request.form.get("topic_name")
    if topic_name in topic_topics:
        del topic_topics[topic_name]
        save_topic_topics(topic_topics)
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


@app.route("/rename_topic_topic", methods=["POST"])
def rename_topic_topic():
    current_topic_name = request.form.get("current_topic_name")
    new_topic_name = request.form.get("new_topic_name")
    # Check if the current topic exists and the new topic name is not empty
    if current_topic_name in topic_topics and new_topic_name:
        # Check if the new topic name already exists
        if new_topic_name in topic_topics:
            return jsonify(
                {"success": False, "message": "The new Topic name already exists."}
            )

        # Rename the Topic by reassigning the topic history
        topic_topics[new_topic_name] = topic_topics[current_topic_name]
        del topic_topics[current_topic_name]
        save_topic_topics(topic_topics)

        return jsonify({"success": True, "message": "Topic renamed successfully."})
    else:
        return jsonify(
            {"success": False, "message": "Topic not found or new topic name is empty."}
        )


# Route to handle topic input from the user and generate GPT-4 response
@app.route("/send_message", methods=["POST"])
def send_message():
    global token_running_total, token_running_total_location
    topic_name = request.form.get("topic_name")
    user_input = request.form.get("user_input")
    message_id = str(uuid.uuid4())
    if topic_name in topic_topics:
        topic_topics[topic_name]["messages"].append(
            {"id": message_id, "user": user_input}
        )

        # Call the GPT-4 API to generate a response (Note: Adjust this for GPT-4 specifications)
        gpt_response = generate_gpt_response(topic_topics[topic_name])
        
        response_id = str(uuid.uuid4())
        topic_topics[topic_name]["messages"].append(
            {"id": response_id, "gpt": gpt_response}
        )
        save_topic_topics(topic_topics)
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
    topic_name = request.form.get("topic_name")
    message_id = request.form.get("message_id")
    if topic_name in topic_topics:
        topic_topics[topic_name]["messages"] = [
            msg for msg in topic_topics[topic_name]["messages"] if msg["id"] != message_id
        ]
        save_topic_topics(topic_topics)
        return jsonify({"success": True, "message": "Message deleted."})
    else:
        return jsonify({"success": False, "message": "Topic not found."})



@app.route('/gpt', methods=['POST'])
def gpt():
    user_text = request.form.get('user_text')
    task_description = request.form.get('task_description')

    if not user_text or not task_description:
        return jsonify({'success': False, 'message': 'User text and task description are required.'})

    try:
        # Construct the prompt for the editing task
        prompt = f"{task_description}\n\nInput: {user_text}\n\nOutput:"
        
        # Use the GPT-3 "text-davinci-edit-001" engine to complete the editing task
        response = openai.Completion.create(
          model="text-davinci-003",
          prompt=prompt,
          max_tokens=100,
          temperature=1
        )

        # Extract the generated text from the API response
        return_text = response.get('choices', [{}])[0].get('text', '').strip()

        return jsonify({
            'success': True,
            'output': return_text.strip('"')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


# Run the Flask application
if __name__ == "__main__":
    import random, threading, webbrowser

    port = 5002
    url = "https://127.0.0.1:{0}".format(port)

    #threading.Timer(1.25, lambda: webbrowser.open(url) ).start()

    app.run(debug=True,host='0.0.0.0',port=port,ssl_context=('cert.pem', 'key.pem'))
