from flask import jsonify
import configparser
import socket
import json

class EngineUDPSender:
    def __init__(self, config_file='config.ini'):
        # Read the config file once upon initialization
        config = configparser.ConfigParser()
        config.read(config_file)

        # Set the IP and Port as instance variables
        self.udp_ip = config.get('engine', 'udp_ip', fallback='127.0.0.1')
        self.udp_port = config.getint('engine', 'udp_port', fallback=5005)

        # Create the socket connection once
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def default_send_to_engine(self, request):
        data = request.json
        self.send_to_engine(data)
        return jsonify({"status": "success", "received": data}), 200

    def send_to_engine(self, data):
        """Encodes and sends data to the configured UDP engine."""
        try:
            message = json.dumps(data).encode('utf-8')
            self.sock.sendto(message, (self.udp_ip, self.udp_port))
        except Exception as e:
            print(f"Error sending to engine: {e}")
    
    def request_from_engine(self, request_payload):
        req_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        req_sock.settimeout(1.0) # Wait a maximum of 1 second for the engine
        
        req_sock.sendto(json.dumps(request_payload).encode('utf-8'), (self.udp_ip, self.udp_port))
        
        try:
            # Wait and listen for the engine to reply (buffer = max UDP
            # datagram size so a large reply can't be truncated)
            data, _ = req_sock.recvfrom(65535)
            engine_state = json.loads(data.decode('utf-8'))
            
            return jsonify({"status": "success", "data": engine_state}), 200
            
        except socket.timeout:
            # If the engine is offline, fail
            return jsonify({"status": "error", "message": "Engine timeout"}), 503

        finally:
            req_sock.close()

engine_sender = EngineUDPSender()