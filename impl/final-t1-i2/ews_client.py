import socket
import threading
import argparse

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--src_ip", default="10.0.26.11", help="IP to listen on")
    parser.add_argument("--src_port", type=int, default=12346, help="Port to listen on")
    parser.add_argument("--dst_ip", default="10.0.26.10")
    parser.add_argument("--dst_port", type=int, default=12346)
    return parser.parse_args()

def client_thread():
    while True:
        response, addr = client_socket.recvfrom(1024)
        response_parsed = response.split("_")

        prefix = response_parsed[0]
        message = response_parsed[1]

        if prefix == "PROTO":
            print message
        elif prefix == "UPDATE":
            message2 = response_parsed[2]
            print message + " - " + message2

def input_thread():
    while True:
        input = raw_input("Input: ")

        if input == "join":
            print "Joining EWS server " + flags.dst_ip + ":" + str(flags.dst_port)
            client_socket.sendto(input, (flags.dst_ip, flags.dst_port))
        elif input == "leave":
            print "Leaving EWS server " + flags.dst_ip + ":" + str(flags.dst_port)
            client_socket.sendto(input, (flags.dst_ip, flags.dst_port))
        elif input == "server":
            print "Server: " + flags.dst_ip + ":" + str(flags.dst_port)
        else:
            print "(join|leave|server)"

if __name__ == '__main__':
    flags = parse_flags()

    print "downstream_client.py started"

    # initialize socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((flags.src_ip, flags.src_port))

    # start threads
    threading.Thread(target=input_thread).start()
    threading.Thread(target=client_thread).start()
