import socket
import time

def udp_client(server_ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            sock.sendto(message.encode(), (server_ip, port))
            print(f"Message sent to {server_ip}:{port}")
            time.sleep(1)  # Sends a message every second
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()

# Server IP and port to send data to
server_ip = "192.168.1.61"
port = 8200
message = "Hello from the module!"

udp_client(server_ip, port, message)
