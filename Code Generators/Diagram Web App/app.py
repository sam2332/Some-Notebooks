from flask import Flask, render_template, request, jsonify
import jsonpickle
app = Flask(__name__)

with open("graph.json",'r') as f:
    app.diagram_data = jsonpickle.decode(f.read())
# Serve the HTML page with the diagram interface
@app.route('/')
def index():
    return render_template('index.html')

# Save the diagram data
@app.route('/save', methods=['POST'])
def save_diagram():
    data = request.json
    print(data)
    # Here, you can save the data to a database or file
    # For simplicity, we'll just store it in memory
    app.diagram_data = data
    with open("graph.json",'w') as f:
        f.write(jsonpickle.encode(data))
    return jsonify({'status': 'success'})



@app.route('/ViewNode', methods=['GET'])
def view_node():
    node_id = request.args.get('id')
    # Fetch data for the node using the provided ID
    
    # Render the modal content template with the fetched data
    return render_template('modal_ViewNode.html', node_id=node_id)


# Restore the diagram data
@app.route('/load', methods=['GET'])
def load_diagram():
    # Here, you would retrieve the data from the storage
    # For simplicity, we'll just return the stored data from memory
    if hasattr(app, 'diagram_data'):
        return jsonify(app.diagram_data)
    else:
        return jsonify({'status': 'error', 'message': 'No diagram data found'})

if __name__ == '__main__':
    app.run(debug=True)