import socket
import struct
import argparse
import time

# Command-line arguments setup
parser = argparse.ArgumentParser(description='UDP Requester')
parser.add_argument('-p', '--port', type=int, required=True, help='Port to listen on')
parser.add_argument('-o', '--file_option', type=str, required=True, help='File name to request')
args = parser.parse_args()

# Create UDP socket and bind it to the specified port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

# Function to request file chunks from a sender
def request_file(sender_address, filename):
    packet_type = b'R'  # 'R' for REQUEST packet
    seq_no = 0  # Sequence number for REQUEST packet is set to 0
    payload_length = 0  # No payload length for REQUEST packet
    packet = struct.pack('!c I H', packet_type, seq_no, payload_length) + filename.encode('utf-8')
    sock.sendto(packet, sender_address)
    print(f"Requested {filename} from {sender_address}")

def receive_file(filename):
    # Create a buffer to store packets as they arrive
    buffer = {}
    start_time = time.time()
    total_data_received = 0
    total_packets_received = 0
    expected_sequence = 0

    while True:
        packet, sender_address = sock.recvfrom(4096)
        packet_type, seq_no, payload_length = struct.unpack('!c I H', packet[:7])
        data = packet[7:7 + payload_length]
        
        if packet_type == b'D':  # DATA packet
            buffer[seq_no] = data
            total_data_received += payload_length
            total_packets_received += 1

            # Print information on the received packet
            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            percentage = (total_data_received / total_file_size) * 100
            print(f"Received packet from {sender_address} - Seq: {seq_no}, Len: {payload_length}, "
                  f"Data: {data[:4]}, {percentage:.2f}% complete")
        
        elif packet_type == b'E':  # END packet
            print(f"END packet received from {sender_address}. File part transfer complete.")
            break

    # After all packets are received, sort them by sequence and write to file
    with open(filename, 'ab') as file:  # Append to the file if multiple senders
        for seq_no in sorted(buffer.keys()):
            file.write(buffer[seq_no])
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n--- Summary for {sender_address} ---")
    print(f"Total packets received: {total_packets_received}")
    print(f"Total data bytes received: {total_data_received}")
    print(f"Average packets/second: {total_packets_received / duration:.2f}")
    print(f"Duration: {duration:.2f} seconds")

def main():
    filename = args.file_option

    # Read tracker file to get sender information
    tracker_info = []
    with open('tracker.txt', 'r') as tracker:
        for line in tracker:
            file_name, id, sender_host, sender_port, file_size = line.split()
            if file_name == filename:
                tracker_info.append((int(id), sender_host, int(sender_port), int(file_size.strip('B'))))
    
    # Sort by ID to ensure parts are requested in the correct order
    tracker_info.sort(key=lambda x: x[0])

    # Request each file part from the appropriate sender
    global total_file_size
    total_file_size = sum(part[3] for part in tracker_info)  # Calculate total file size from all parts
    print(f"Total file size to receive: {total_file_size} bytes")

    for id, sender_host, sender_port, file_size in tracker_info:
        sender_address = (sender_host, sender_port)
        request_file(sender_address, filename)
        receive_file(filename)

    print("\nFile transfer complete. All parts received and assembled.")

if __name__ == '__main__':
    main()
