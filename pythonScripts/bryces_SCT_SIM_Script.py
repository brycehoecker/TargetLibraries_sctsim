import socket

def udp_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    print(f"Server listening on {ip}:{port}")

    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        print(f"Received message: {data} from {addr}")

try:
    udp_server("192.168.1.61", 8200)
except Exception as e:
    print(f"An error occurred: {e}")
