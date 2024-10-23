from flask import Flask, jsonify, request
from queue import Queue

app = Flask(__name__)

# Erstellen einer Queue für Steueranweisungen
command_queue = Queue()

# Route zum Hinzufügen von Anweisungen zur Queue, sowohl über GET als auch POST
@app.route('/add_command', methods=['POST', 'GET'])
def add_command():
    if request.method == 'POST':
        # Bei einer POST-Anfrage erwarten wir JSON-Daten
        command = request.get_json()
    elif request.method == 'GET':
        # Bei einer GET-Anfrage lesen wir Parameter aus der URL
        command = {
            "type": request.args.get('type'),
            "action": request.args.get('action'),
            "x": request.args.get('x'),
            "y": request.args.get('y'),
            "button": request.args.get('button'),
            "key": request.args.get('key')
        }

        # Verarbeite Modifikatoren, die als Liste von Werten in der URL angegeben werden
        modifiers = request.args.get('modifiers')
        if modifiers:
            command["modifiers"] = modifiers.split(',')  # Modifikatoren in Liste umwandeln
        
        # Filtere None-Werte heraus
        command = {k: v for k, v in command.items() if v is not None}
    
    # Überprüfen, ob ein gültiger Befehl vorhanden ist
    if command:
        command_queue.put(command)
        return jsonify({'message': 'Command added successfully'}), 200
    else:
        return jsonify({'error': 'Invalid command'}), 400

# Route zum Abrufen des nächsten Befehls aus der Queue
@app.route('/next_command', methods=['GET'])
def next_command():
    if not command_queue.empty():
        command = command_queue.get()
        return jsonify(command)
    else:
        return jsonify({'message': 'No commands available'}), 204

if __name__ == '__main__':
    # Server auf einem bestimmten Port starten
    app.run(host='0.0.0.0', port=5000)
