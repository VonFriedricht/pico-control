import time
import wifi
import socketpool
import adafruit_requests
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from secrets import secrets

# WLAN verbinden
print("Verbinde mit WLAN...")
wifi.radio.connect(secrets['ssid'], secrets['password'])
print("Verbunden mit", secrets['ssid'])
print("IP-Adresse:", wifi.radio.ipv4_address)

# Socket-Pool und HTTP Session erstellen
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

url = "http://<add something here>:8080/next_command"

# USB-HID Tastatur und Maus initialisieren
keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# Define a "home" reset point (you can pick any point that is consistent, e.g. top-left)
RESET_POINT = (-1500, -1500)  # Eine Bewegung weit nach links oben zum "Ankern"

while True:
    try:
        # Abrufen des nächsten Befehls
        response = requests.get(url)

        if response.status_code == 200:
            command = response.json()

            # Dauer festlegen (Standardwert, falls nicht angegeben)
            duration = float(command.get('duration', 0.1))  # Standard 0.1 Sekunden

            # Anweisungen verarbeiten
            if command['type'] == 'keyboard':
                key = command['key']

                # Buchstaben 'a'-'z' umsetzen, Pfeiltasten verarbeiten, ESC, Windows oder Home-Taste erkennen
                if key.isalpha() and len(key) == 1:
                    keycode = getattr(Keycode, key.upper())  # 'a' -> Keycode.A
                    keyboard.press(keycode)
                    print(f"Taste '{key}' wurde gedrückt.")
                    time.sleep(duration)
                    keyboard.release(keycode)
                    print(f"Taste '{key}' wurde nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'up':
                    keyboard.press(Keycode.UP_ARROW)
                    print("Pfeiltaste nach oben gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.UP_ARROW)
                    print(f"Pfeiltaste nach oben nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'down':
                    keyboard.press(Keycode.DOWN_ARROW)
                    print("Pfeiltaste nach unten gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.DOWN_ARROW)
                    print(f"Pfeiltaste nach unten nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'left':
                    keyboard.press(Keycode.LEFT_ARROW)
                    print("Pfeiltaste nach links gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.LEFT_ARROW)
                    print(f"Pfeiltaste nach links nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'right':
                    keyboard.press(Keycode.RIGHT_ARROW)
                    print("Pfeiltaste nach rechts gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.RIGHT_ARROW)
                    print(f"Pfeiltaste nach rechts nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'esc' or key.lower() == 'escape':
                    keyboard.press(Keycode.ESCAPE)
                    print("Escape-Taste gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.ESCAPE)
                    print(f"Escape-Taste nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'win' or key.lower() == 'windows':
                    keyboard.press(Keycode.GUI)
                    print("Windows-Taste gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.GUI)
                    print(f"Windows-Taste nach {duration} Sekunden losgelassen.")
                elif key.lower() == 'home':
                    keyboard.press(Keycode.HOME)
                    print("Home-Taste gedrückt.")
                    time.sleep(duration)
                    keyboard.release(Keycode.HOME)
                    print(f"Home-Taste nach {duration} Sekunden losgelassen.")
                else:
                    print("Unbekannte Tasteneingabe:", key)

            elif command['type'] == 'mouse':
                # Mausanweisung verarbeiten
                if command['action'] == 'move':
                    # Maus zuerst zum Reset-Punkt "springen", um eine konsistente Basis zu schaffen
                    mouse.move(x=RESET_POINT[0], y=RESET_POINT[1])
                    time.sleep(0.1)  # Kleine Pause, damit die Bewegung registriert wird

                    # Anschließend zur Zielposition relativ bewegen
                    target_x = int(command['x'])
                    target_y = int(command['y'])
                    
                    mouse.move(x=target_x, y=target_y)
                    print(f"Maus bewegt zu (x: {target_x}, y: {target_y})")

                elif command['action'] == 'click':
                    # Mausklick verarbeiten
                    button = command['button']
                    
                    # Modifikatoren verarbeiten (falls vorhanden)
                    if 'modifiers' in command:
                        modifiers = command['modifiers']
                        for modifier in modifiers:
                            if modifier == 'shift':
                                keyboard.press(Keycode.SHIFT)
                                print("Shift gedrückt.")
                            elif modifier == 'ctrl':
                                keyboard.press(Keycode.CONTROL)
                                print("Control gedrückt.")
                            elif modifier == 'alt':
                                keyboard.press(Keycode.ALT)
                                print("Alt gedrückt.")

                    # Klick ausführen
                    if button == 'left':
                        mouse.press(Mouse.LEFT_BUTTON)
                        print("Linksklick gedrückt.")
                    elif button == 'right':
                        mouse.press(Mouse.RIGHT_BUTTON)
                        print("Rechtsklick gedrückt.")
                    else:
                        print("Unbekannter Klicktyp:", button)

                    # Warte für die angegebene Dauer
                    time.sleep(duration)

                    # Klick loslassen
                    if button == 'left':
                        mouse.release(Mouse.LEFT_BUTTON)
                        print(f"Linksklick nach {duration} Sekunden losgelassen.")
                    elif button == 'right':
                        mouse.release(Mouse.RIGHT_BUTTON)
                        print(f"Rechtsklick nach {duration} Sekunden losgelassen.")

                    # Modifikatoren loslassen (falls vorhanden)
                    if 'modifiers' in command:
                        for modifier in command['modifiers']:
                            if modifier == 'shift':
                                keyboard.release(Keycode.SHIFT)
                                print("Shift losgelassen.")
                            elif modifier == 'ctrl':
                                keyboard.release(Keycode.CONTROL)
                                print("Control losgelassen.")
                            elif modifier == 'alt':
                                keyboard.release(Keycode.ALT)
                                print("Alt losgelassen.")

        elif response.status_code == 204:
            # Keine Befehle verfügbar
            print("Keine neuen Befehle in der Queue.")
        
    except Exception as e:
        print("Fehler:", e)

    # Warte für kurze Zeit bevor die nächste Anfrage gestellt wird
    time.sleep(1)
