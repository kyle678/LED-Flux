import socket
import select
import json
import traceback
import configparser

from engine.controller import Controller
from engine.handlers import COMMAND_HANDLERS

CONFIG_FILE = 'config.ini'

def load_config(config_file):
    config = configparser.ConfigParser()
    # read() returns the list of files it could parse; missing files are
    # skipped silently, so warn here and fall back to defaults
    if not config.read(config_file):
        print(f"Config file '{config_file}' not found, using defaults.")
    return config

def set_up_socket_server(udp_ip, udp_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))
    sock.setblocking(0) # Make socket non-blocking
    return sock

def respond_to_socket(sock, addr, message):
    response_message = json.dumps(message).encode('utf-8')
    sock.sendto(response_message, addr)

def check_for_api_commands(sock):
    ready = select.select([sock], [], [], 0.01) # Wait max 10ms
    if ready[0]:
        data, addr = sock.recvfrom(8192)
        try:
            command = json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Ignoring malformed packet from {addr}: {e}")
            return None, None
        if not isinstance(command, dict):
            print(f"Ignoring non-object command from {addr}: {command!r}")
            return None, None
        return command, addr
    return None, None

def dispatch_command(sock, addr, controller, command):
    action = command.get("action")

    # Look up the handler function in the dictionary
    handler = COMMAND_HANDLERS.get(action)

    if not handler:
        print(f"Received unknown action: {action}")
        return

    if action == "get_status":
        current_state = handler(controller)
        respond_to_socket(sock, addr, current_state)
    else:
        handler(controller, command.get("data", {}))

def loop(sock, controller):
    while True:
        command, addr = check_for_api_commands(sock)

        if command:
            try:
                dispatch_command(sock, addr, controller, command)
            except Exception:
                print(f"Error handling command {command}:")
                traceback.print_exc()

        try:
            controller.update()
        except Exception:
            # A broken animation would raise every frame; drop the
            # animations so the engine stays responsive to new commands.
            print("Error rendering frame, clearing animations:")
            traceback.print_exc()
            controller.animations = []

def main():

    config = load_config(CONFIG_FILE)

    PIN_NUMBER = config.getint('pixels', 'pin_number', fallback=18)
    NUM_PIXELS = config.getint('pixels', 'num_pixels', fallback=10)
    BRIGHTNESS = config.getfloat('pixels', 'brightness', fallback=0.2)

    # Same section and fallbacks the API reads in udp_comms.py, so the two
    # processes can't disagree when config.ini changes
    UDP_IP = config.get('engine', 'udp_ip', fallback='127.0.0.1')
    UDP_PORT = config.getint('engine', 'udp_port', fallback=5005)

    sock = set_up_socket_server(UDP_IP, UDP_PORT)

    controller = Controller(num_pixels=NUM_PIXELS, pin=PIN_NUMBER, brightness=BRIGHTNESS)

    print("LED Engine running...")

    loop(sock, controller)

if __name__ == '__main__':
    main()