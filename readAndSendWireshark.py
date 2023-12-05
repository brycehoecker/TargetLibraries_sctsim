from scapy.all import rdpcap, IP, sendp

# Path to your Wireshark capture file
capture_file = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/Run_Wireshark_Capture.pcapng"

# Read the capture file
packets = rdpcap(capture_file)

for packet in packets:
    if IP in packet:
        # Change the destination IP address
        packet[IP].dst = "192.168.1.61"

        # Send the packet
        sendp(packet)

