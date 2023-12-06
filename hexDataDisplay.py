import os
import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar

# Set the directory here
directory = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/Run_Wireshark_Capture"

def find_packet_files(directory, limit=100):
    """Finds packet files in the specified directory, up to the specified limit."""
    files = []
    for i in range(1, limit + 1):
        filename = os.path.join(directory, f"packet_{i}.txt")
        if os.path.exists(filename):
            files.append(filename)
        else:
            break
    return files

def read_file_data(filename):
    """Reads data from a file."""
    with open(filename, 'r') as file:
        return file.read().strip()

def display_data_in_gui(data):
    """Displays each data row in a scrollable Tkinter window."""
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

    for i, row in enumerate(data):
        label = tk.Label(scrollable_frame, text=f"File {i+1}: {row}", anchor="w")
        label.pack(fill='x', padx=10, pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    root.mainloop()

def main():
    if os.path.isdir(directory):
        packet_files = find_packet_files(directory)
        packet_data = [read_file_data(filename) for filename in packet_files]
        display_data_in_gui(packet_data)
    else:
        print(f"The directory '{directory}' does not exist. Exiting.")

if __name__ == "__main__":
    main()
