import socket
import select
import json
import configparser

from engine.controller import Controller
from engine.handlers import COMMAND_HANDLERS

CONFIG_FILE = 'config.ini'

def load_config(config_file):
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        return config
    except FileNotFoundError:
        return FileNotFoundError("Configuration file not found.")

def set_up_socket_server():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5005
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(0) # Make socket non-blocking
    return sock

def respond_to_socket(sock, addr, message):
    response_message = json.dumps(message).encode('utf-8')
    sock.sendto(response_message, addr)

def check_for_api_commands(sock):
    ready = select.select([sock], [], [], 0.01) # Wait max 10ms
    if ready[0]:
        data, addr = sock.recvfrom(8192)
        command = json.loads(data.decode('utf-8'))
        return command, addr
    return None, None

def loop(sock, controller):
    while True:
        command, addr = check_for_api_commands(sock)
        
        if command:
            action = command.get("action")

            # Look up the handler function in the dictionary
            handler = COMMAND_HANDLERS.get(action)

            if action == "get_status":
                current_state = handler(controller)
                respond_to_socket(sock, addr, current_state)
            else:
                data = command.get("data", {})
                
                if handler:
                    # Execute the function
                    handler(controller, data)
                else:
                    print(f"Received unknown action: {action}")
                
        controller.update()

def main():

    config = load_config(CONFIG_FILE)

    PIN_NUMBER = config.getint('pixels', 'pin_number', fallback=18)
    NUM_PIXELS = config.getint('pixels', 'num_pixels', fallback=10)
    BRIGHTNESS = config.getfloat('pixels', 'brightness', fallback=0.2)

    sock = set_up_socket_server()

    controller = Controller(num_pixels=NUM_PIXELS, pin=PIN_NUMBER, brightness=BRIGHTNESS)

    print("LED Engine running...")

    loop(sock, controller)

if __name__ == '__main__':
    main()