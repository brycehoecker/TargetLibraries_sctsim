import pyshark

def hex_to_binary(hex_string):
    # Remove colons from the hex string
    clean_hex_string = hex_string.replace(':', '')
    # Convert hex to binary
    binary_string = bin(int(clean_hex_string, 16))[2:]
    return binary_string.zfill(len(clean_hex_string) * 4)  # Ensure it's padded to the correct length

def capture_packets_to_binary_files(file_path, start, end, output_directory):
    # Load the capture file
    capture = pyshark.FileCapture(file_path)

    packet_number = 0

    # Iterate over each packet
    for packet in capture:
        packet_number += 1

        # Process only packets within the specified range
        if start <= packet_number <= end:
            # Extract hex data from the packet
            try:
                hex_data = packet.layers[-1]._all_fields.get('data.data')
                if hex_data:
                    print(f'Packet {packet_number} Hex Data: {hex_data}')

                    binary_data = hex_to_binary(hex_data)
                    print(f'Packet {packet_number} Binary Data: {binary_data}')

                    # Write the binary data to a file
                    output_file_path = f'{output_directory}/packet_{packet_number}.bin'
                    with open(output_file_path, 'w') as file:
                        file.write(binary_data)

                    print(f'Packet {packet_number} written to {output_file_path}')
                else:
                    print(f'No hex data found in packet {packet_number}')
            except AttributeError:
                print(f'No hex data found in packet {packet_number}')
        elif packet_number > end:
            # Stop processing once the end of the range is reached
            break
            
# User input for file path, start and end packet numbers, and output directory
file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/Run_Wireshark_Capture.pcapng"
output_directory = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir"
start = int(input("Enter the start packet number: "))
end = int(input("Enter the end packet number: "))

capture_packets_to_binary_files(file_path, start, end, output_directory)




