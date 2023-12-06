import os
import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar

# Set the directory here
directory = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/Run_Wireshark_Capture"

def find_packet_files(directory, start=5000, end=5750):
    """Finds packet files in the specified directory, from start to end numbers."""
    files = []
    for i in range(start, end + 1):
        filename = os.path.join(directory, f"packet_{i}.txt")
        if os.path.exists(filename):
            files.append(filename)
        return files

def read_file_data(filename):
    """Reads data from a file."""
    with open(filename, 'r') as file:
        return file.read().strip()

def display_data_in_gui(data, start_index):
    """Displays a subset of the data in a scrollable Tkinter window."""
    root = tk.Tk()
    root.title("Packet Data Viewer")

    canvas = Canvas(root)
    scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    for i, row in enumerate(data[start_index:start_index + 100]):  # Display only 100 files at a time
        label = tk.Label(scrollable_frame, text=f"File {start_index + i}: {row}", anchor="w")
        label.pack(fill='x', padx=10, pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    root.mainloop()

def main():
    if os.path.isdir(directory):
        packet_files = find_packet_files(directory)
        packet_data = [read_file_data(filename) for filename in packet_files]
        
        # You can change this index to display different sets of 100 files
        start_index = 0
        display_data_in_gui(packet_data, start_index)
    else:
        print(f"The directory '{directory}' does not exist. Exiting.")

if __name__ == "__main__":
    main()
