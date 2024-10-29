import cv2
import time
from datetime import datetime
from queue import Queue
import numpy as np
from flask import Flask, request, jsonify, send_file
import os

print("Skript gestartet", flush=True)
app = Flask(__name__)
command_queue = Queue()
gameId = ""
targetStatus = "login"

def pruefe_template(frame, template):
    if template is None or frame.shape[0] < template.shape[0] or frame.shape[1] < template.shape[1]:
        print("Fehler: Template ist größer als das aktuelle Frame oder nicht geladen.", flush=True)
        return False
    
    res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)
    return len(loc[0]) > 0

def pruefe_template_pos(frame, template):
    if template is None or frame.shape[0] < template.shape[0] or frame.shape[1] < template.shape[1]:
        print("Fehler: Template ist größer als das aktuelle Frame oder nicht geladen.", flush=True)
        return False, None
    
    res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        return True, max_loc
    else:
        return False, None

tselect = cv2.imread('/home/raspi/pystart/templates/gameselect2.png', 0)
tstart = cv2.imread('/home/raspi/pystart/templates/gamestart.jpg', 0)
tpw = cv2.imread('/home/raspi/pystart/templates/pw1.jpg', 0)
tmenu = cv2.imread('/home/raspi/pystart/templates/menu.jpg', 0)
tpressanykey = cv2.imread('/home/raspi/pystart/templates/pressanykey.jpg', 0)
tcore = cv2.imread('/home/raspi/pystart/templates/core.png', 0)

time.sleep(10)
cap = cv2.VideoCapture(0)

@app.route('/screenshot', methods=['GET'])
def api_screenshot():
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            filename = '/home/raspi/pystart/last_screenshot.jpg'
            cv2.imwrite(filename, frame)
            print("Screenshot erzwungen und gespeichert.", flush=True)
            return send_file(filename, mimetype='image/jpeg')
        else:
            return jsonify({"status": "error", "message": "Fehler: Kein Frame erhalten"}), 500
    else:
        return jsonify({"status": "error", "message": "Fehler: Kamera konnte nicht geöffnet werden"}), 500

@app.route('/flush_log', methods=['GET'])
def flush_log():
    log_file_path = '/home/raspi/pystart/print.log'
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            lines = file.readlines()
        
        # Keep only the last 10 lines
        lines_to_keep = lines[-10:]
        
        with open(log_file_path, 'w') as file:
            file.writelines(lines_to_keep)
        
        return jsonify({"status": "success", "message": "Log flushed, kept last 10 lines"}), 200
    else:
        return jsonify({"status": "error", "message": "Log file not found"}), 404

@app.route('/add_command', methods=['POST', 'GET'])
def add_command():
    if request.method == 'POST':
        command = request.get_json()
    elif request.method == 'GET':
        command = {
            "type": request.args.get('type'),
            "action": request.args.get('action'),
            "x": request.args.get('x'),
            "y": request.args.get('y'),
            "button": request.args.get('button'),
            "text": request.args.get('text'),
            "key": request.args.get('key'),
            "duration": request.args.get('duration')
        }
        modifiers = request.args.get('modifiers')
        if modifiers:
            command["modifiers"] = modifiers.split(',')
        keys = request.args.get('keys')
        if keys:
            command["keys"] = keys.split(',')
        command = {k: v for k, v in command.items() if v is not None}
    if command:
        command_queue.put(command)
        return jsonify({'message': 'Command added successfully'}), 200
    else:
        return jsonify({'error': 'Invalid command'}), 400

@app.route('/next_command', methods=['GET'])
def next_command():
    if not command_queue.empty():
        command = command_queue.get()
        return jsonify(command)
    else:
        return jsonify({'message': 'No commands available'}), 204

def keypress(*key):
    key = list(key)
    print("Tastendruck:", key, flush=True)
    if not isinstance(key, list):
        key = [key]
    for k in key:
        if isinstance(k, list):
            command_queue.put({"type": "keyboard", "keys": ",".join(k)})
        elif "," in k:
            command_queue.put({"type": "keyboard", "keys": k})
        else:
            command_queue.put({"type": "keyboard", "key": k})
        
def mouseclick(x=0, y=0, button="left"):
    command_queue.put({"type": "mouse", "action":"move", "x": x/1.5, "y": y/1.5})
    if button != None:
        command_queue.put({"type": "mouse", "action":"click", "button": button})

def write_text(text=""):
    command_queue.put({"type": "text", "text": text})


@app.route('/join', methods=['GET'])
def join_game():
    global gameId
    gameId = request.args.get('gameId')
    return jsonify({'message': 'Game joined successfully'}), 200

@app.route('/view_commands', methods=['GET'])
def view_commands():
    commands = list(command_queue.queue)
    return jsonify(commands), 200

### Ingame
@app.route('/look_down', methods=['GET'])
def look_down():
    mouseclick(640*1.5, 640, None)
    return jsonify({'message': 'Looked down'}), 200
    
@app.route('/look_left', methods=['GET'])
def look_left():
    mouseclick(320, 540, None)
    return jsonify({'message': 'Looked left'}), 200

@app.route('/look_right', methods=['GET'])
def look_right():
    mouseclick(960*1.5, 540, None)
    return jsonify({'message': 'Looked right'}), 200

@app.route('/login', methods=['GET'])
def login():
    global targetStatus
    targetStatus = "login"
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/logout', methods=['GET'])
def logout():
    global targetStatus
    targetStatus = "logout"
    keypress("esc")
    mouseclick(220,999)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/move_one_chest_left', methods=['GET'])
def move_one_chest_left():
    command_queue.put({"type": "keyboard", "keys": "w,a", "duration": 1})
    command_queue.put({"type": "keyboard", "keys": "s", "duration": 1})
    return jsonify({'message': 'Moved one chest left'}), 200

@app.route('/move_one_chest_right', methods=['GET'])
def move_one_chest_right():
    command_queue.put({"type": "keyboard", "keys": "w,d", "duration": 1})
    command_queue.put({"type": "keyboard", "keys": "s", "duration": 1})
    return jsonify({'message': 'Moved one chest right'}), 200

@app.route('/identify_chest', methods=['GET'])
def identify_chest():
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            templates = {
                "icon1": cv2.imread('/home/raspi/pystart/templates/chestpaste_icon.png', 0),
                "icon2": cv2.imread('/home/raspi/pystart/templates/schmelzen_icon.png', 0),
                "icon3": cv2.imread('/home/raspi/pystart/templates/schmelzen_icon.png', 0)
            }
            for name, template in templates.items():
                found, position = pruefe_template_pos(gray_frame, template)
                if found:
                    return jsonify({"status": "success", "chest_type": name, "position": position}), 200
            return jsonify({"status": "error", "message": "Kein passendes Template gefunden"}), 404
        else:
            return jsonify({"status": "error", "message": "Fehler: Kein Frame erhalten"}), 500
    else:
        return jsonify({"status": "error", "message": "Fehler: Kamera konnte nicht geöffnet werden"}), 500

@app.route('/crop_frame', methods=['GET'])
def crop_frame():
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    width = int(request.args.get('width'))
    height = int(request.args.get('height'))
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cropped_frame = frame[y:y+height, x:x+width]
            filename = '/home/raspi/pystart/cropped_frame.jpg'
            cv2.imwrite(filename, cropped_frame)
            return send_file(filename, mimetype='image/jpeg')
        else:
            return jsonify({"status": "error", "message": "Fehler: Kein Frame erhalten"}), 500
    else:
        return jsonify({"status": "error", "message": "Fehler: Kamera konnte nicht geöffnet werden"}), 500

def crop_and_hash(positions, width, height):
    if not positions:
        return {"status": "error", "message": "No positions provided"}, 400

    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            results = []
            for pos in positions:
                x, y = pos['x'], pos['y']
                cropped_frame = gray_frame[y:y+height, x:x+width]
                
                # Remove brown background (assuming brown is in a certain range)
                lower_brown = np.array([10, 100, 20])
                upper_brown = np.array([20, 255, 200])
                mask = cv2.inRange(cropped_frame, lower_brown, upper_brown)
                cropped_frame[mask != 0] = [0, 0, 0]
                
                # Apply blur
                blurred_frame = cv2.GaussianBlur(cropped_frame, (5, 5), 0)
                
                # Compute hash
                hash_value = hash(blurred_frame.tobytes())
                results.append({"position": pos, "hash": hash_value})
            
            return {"status": "success", "results": results}, 200
        else:
            return {"status": "error", "message": "Fehler: Kein Frame erhalten"}, 500
    else:
        return {"status": "error", "message": "Fehler: Kamera konnte nicht geöffnet werden"}, 500

@app.route('/crop_and_hash', methods=['GET'])
def api_crop_and_hash():
    positions = request.args.get('positions')
    if positions:
        positions = [{"x": int(pos.split(',')[0]), "y": int(pos.split(',')[1])} for pos in positions.split(';')]
    else:
        positions = []
    width = int(request.args.get('width'))
    height = int(request.args.get('height'))
    return jsonify(*crop_and_hash(positions, width, height))

### Main

if __name__ == '__main__':
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=80, debug=False))
    flask_thread.daemon = True
    flask_thread.start()

    if not cap.isOpened():
        print("Fehler: Kamera konnte nicht geöffnet werden", flush=True)
    else:
        no_frame_counter = 0
        while True:
            ret, frame = cap.read()
            if ret:
                no_frame_counter = 0
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                print(f"Current targetStatus: {targetStatus}", flush=True)

                if pruefe_template(gray_frame, tstart) and targetStatus == "login":
                    print("tstart gefunden", flush=True)
                    keypress("enter")

                if pruefe_template(gray_frame, tselect) and targetStatus == "login":
                    print("tselect gefunden", flush=True)
                    keypress("enter")
                  
                if pruefe_template(gray_frame, tmenu) and targetStatus == "login":
                    print("tmenu gefunden", flush=True)
                  
                if pruefe_template(gray_frame, tpw):
                    print("tpw gefunden", flush=True)
                    command_queue = Queue()
                    keypress("left","right","left","right","left","right")

                if pruefe_template(gray_frame, tcore):
                    print("tcore gefunden", flush=True)
                    if targetStatus == "login":
                        command_queue = Queue()
                        mouseclick(180,500)
                        mouseclick(180,500)
                        mouseclick(640,350)
                        mouseclick(640,320)
                    if targetStatus == "logout":
                        command_queue = Queue()
                        mouseclick(190,910)
                        mouseclick(190,910)


                if pruefe_template(gray_frame, tpressanykey):
                    print("tpressanykey gefunden", flush=True)
                    #mouseclick(180,500)
                    #keypress(["enter"])
                  

                time.sleep(10)
            else:
                no_frame_counter += 1
                wait_time = min(60 * no_frame_counter, 3600)
                print(f"Fehler: Kein Frame erhalten, warte {wait_time} Sekunden", flush=True)
                time.sleep(wait_time)

    cap.release()
    cv2.destroyAllWindows()
