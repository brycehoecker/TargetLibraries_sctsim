import ctypes
import target_driver as td
from target_driver import UDPServer as udps
#import target_io as ti
#import target_calib as tc

## Open a file for writing (you can replace 'output.txt' with your desired file name)
#with open('TD_from_swig.txt', 'w') as file:
#    # Redirect the standard output to the file
#    import sys
#    original_stdout = sys.stdout
#    sys.stdout = file
#    
#    # Print the output of help(td) to the file
#    print("Target Driver Functions", help(td))
#    
#    # Restore the standard output
#    sys.stdout = original_stdout
#
# The output of help(td) has been written to 'output.txt'

# Create an instance of the UDPServer
my_server = udps("192.168.1.1", 8080, 9090, 100)

# Setup the server (if needed)
my_server.Setup("192.168.1.1", 8080, 9090, 100)

# Send a data packet
data = "Your data here".encode()  # Encode string to bytes
buffer = ctypes.create_string_buffer(data)
length = len(data)

# Pass the buffer as a pointer
pointer = ctypes.cast(ctypes.byref(buffer), ctypes.c_void_p)
result = my_server.SendDataPacket(pointer, length)

# Send a response
response_data = b"Response data here"
response_length = len(response_data)
response_result = my_server.SendResponse(response_data, response_length)

# Close the socket when done
my_server.CloseSocket()
