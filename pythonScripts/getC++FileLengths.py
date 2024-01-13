import csv
import os

def count_lines_of_code_and_save_to_csv(directory, output_csv_file, subfolders):
    # Define C/C++ file extensions
    extensions = ['.c', '.cc', '.cpp', '.h', '.hh', '.hpp']

    # Mapping for subfolder names to display in the CSV
    subfolder_display_names = {
        'targetdriver-issue37423': 'TargetDriver',
        'targetio-pSCT': 'TargetIO',
        'targetcalib-pSCT': 'TargetCalib'
    }

    # Create dictionaries to store file paths, line counts, and subfolder info
    line_counts = {subfolder: {} for subfolder in subfolders}

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file has a valid C/C++ extension
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)

                # Determine which subfolder the file belongs to
                subfolder_name = next((sf for sf in subfolders if sf in file_path), None)
                if subfolder_name:
                    try:
                        # Count lines in the file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Adjust the file path to be relative to the current directory
                            relative_file_path = os.path.relpath(file_path, start=directory)
                            line_counts[subfolder_name][relative_file_path] = sum(1 for _ in f)
                    except Exception as e:
                        print(f"Error reading file {relative_file_path}: {e}")

    # Write results to a CSV file
    with open(output_csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Subfolder', 'File Name', 'Line Count', 'File Path'])
        for subfolder in subfolders:
            display_name = subfolder_display_names.get(subfolder, subfolder)
            for file_path, count in sorted(line_counts[subfolder].items(), key=lambda item: item[1], reverse=True):
                file_name = os.path.basename(file_path)
                writer.writerow([display_name, file_name, count, file_path])

# Define the directory you want to scan
directory = os.getcwd()

# Define the subfolders of interest
subfolders = ['targetdriver-issue37423', 'targetio-pSCT', 'targetcalib-pSCT']

# Usage example
output_csv_file = 'code_line_counts.csv'
count_lines_of_code_and_save_to_csv(directory, output_csv_file, subfolders)

print("CSV file created:", output_csv_file)
