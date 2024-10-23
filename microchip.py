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

            # Anweisungen verarbeiten
            if command['type'] == 'keyboard':
                key = command['key']

                # Buchstaben 'a'-'z' umsetzen
                if key.isalpha() and len(key) == 1:
                    keycode = getattr(Keycode, key.upper())  # 'a' -> Keycode.A
                    keyboard.press(keycode)
                    time.sleep(0.1)
                    keyboard.release(keycode)
                    print(f"Taste '{key}' wurde gedrückt.")
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
                        mouse.click(Mouse.LEFT_BUTTON)
                        print("Linksklick ausgeführt.")
                    elif button == 'right':
                        mouse.click(Mouse.RIGHT_BUTTON)
                        print("Rechtsklick ausgeführt.")
                    else:
                        print("Unbekannter Klicktyp:", button)

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

