import socket
import struct
import argparse
import time

# Command-line arguments setup
parser = argparse.ArgumentParser(description='UDP Sender')
parser.add_argument('-p', '--port', type=int, required=True, help='Port to listen on')
parser.add_argument('-g', '--requester_port', type=int, required=True, help='Requester port')
parser.add_argument('-r', '--rate', type=int, required=True, help='Packets per second rate')
parser.add_argument('-q', '--seq_no', type=int, required=True, help='Initial sequence number')
parser.add_argument('-l', '--length', type=int, required=True, help='Payload length in bytes')
args = parser.parse_args()

# Create UDP socket
# Create UDP socket and bind it to the specified listening port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', args.port))  # Listen on the port specified by the -p argument

def send_data_packet(address, sequence, data):
    packet_type = b'D'  # 'D' for DATA packet
    seq_network_order = socket.htonl(sequence)
    payload_length = len(data)
    packet = struct.pack('!c I H', packet_type, seq_network_order, payload_length) + data
    sock.sendto(packet, address)
    print(f"Sent packet to {address} - Sequence: {sequence}, Data: {data[:4]}")

def main():
    # Requester address using the requester port provided in the argument
    requester_address = ('localhost', args.requester_port)  # Assuming localhost for simplicity; change as needed

    print(f"Listening for requests on port {args.port}...")

    # Receive the request packet from the requester
    request_packet, requester_address = sock.recvfrom(1024)
    
    # Unpack the request packet
    packet_type, seq_no, payload_length = struct.unpack('!c I H', request_packet[:7])
    
    # Extract the filename from the remaining part of the payload
    filename = request_packet[7:].decode('utf-8')
    print(f"Received request for file: {filename} from {requester_address}")
    
    # Open the requested file and start sending data packets
    sequence = args.seq_no
    try:
        with open(filename, "rb") as file:
            while True:
                data = file.read(args.length)
                if not data:
                    break
                send_data_packet(requester_address, sequence, data)
                sequence += len(data)  # Increment sequence by the length of data sent
                time.sleep(1 / args.rate)  # Rate control for packets per second
                
        # Send END packet
        end_packet = struct.pack('!c I H', b'E', socket.htonl(sequence), 0)
        sock.sendto(end_packet, requester_address)
        print("Sent END packet")
        
    except FileNotFoundError:
        print(f"File {filename} not found. Sending END packet.")
        end_packet = struct.pack('!c I H', b'E', socket.htonl(sequence), 0)
        sock.sendto(end_packet, requester_address)
    
    finally:
        sock.close()

if __name__ == '__main__':
    main()
