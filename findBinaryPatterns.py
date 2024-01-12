import re
import os

# ANSI color codes
GREEN = '\033[92m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def read_binary_file_as_string(file_path):
    with open(file_path, "r") as file:
        binary_data = file.read().strip()
    return binary_data

def pattern_to_regex(pattern):
    return pattern.replace('x', '.')

def highlight_matches(data, pattern, line_length=80):
    regex_pattern = pattern_to_regex(pattern)
    highlighted_data = ''
    last_index = 0
    current_line_length = 0  # Current length of the line in terms of visible characters

    for match in re.finditer(regex_pattern, data):
        start, end = match.start(), match.end()
        before_match = data[last_index:start]
        
        # Process the segment before the match
        for char in before_match:
            highlighted_data += char
            current_line_length += 1
            if current_line_length == line_length:
                highlighted_data += '\n'
                current_line_length = 0

        # Highlight the matched segment
        for i in range(start, end):
            if pattern[i - start] != 'x':
                to_add = GREEN + data[i] + ENDC
            else:
                to_add = BLUE + data[i] + ENDC

            highlighted_data += to_add
            current_line_length += 1
            if current_line_length == line_length:
                highlighted_data += '\n'
                current_line_length = 0

        last_index = end

    # Process any remaining data after the last match
    remaining_data = data[last_index:]
    for char in remaining_data:
        highlighted_data += char
        current_line_length += 1
        if current_line_length == line_length:
            highlighted_data += '\n'
            current_line_length = 0

    # Add a newline if the last line is not empty and does not end with a newline
    if current_line_length > 0 and not highlighted_data.endswith('\n'):
        highlighted_data += '\n'

    return highlighted_data

def find_specific_patterns(binary_data, patterns, line_length):
    found_patterns = {}
    for pattern in patterns:
        highlighted_data = highlight_matches(binary_data, pattern, line_length)
        if highlighted_data != binary_data:  # There was a match
            found_patterns[pattern] = highlighted_data
    return found_patterns

def remove_ansi_codes(text):
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)

def main():
    file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir/packet_5640.bin"
    binary_data = read_binary_file_as_string(file_path)

    bits_per_line = int(input("Enter the number of bits to display per line: "))

    print("Binary Data from File:")
    print('\n'.join([binary_data[i:i + bits_per_line] for i in range(0, len(binary_data), bits_per_line)]))

    specific_patterns = [
        "x000xxxxxxxxxxxxx001xxxxxxxxxxxxx010xxxxxxxxxxxxx011xxxxxxxxxxxxx100xxxxxxxxxxxxx101xxxxxxxxxxxxx110xxxxxxxxxxxxx111xxxxxxxxxxxx",
        # Add more patterns as needed
    ]

    found_specific_patterns = find_specific_patterns(binary_data, specific_patterns, bits_per_line)

    print("\nHighlighted Specific Patterns:")
    for pattern, highlighted in found_specific_patterns.items():
        print(f"Pattern: {pattern}\n{highlighted}\n")

    # Ask if the user wants to save the output to a file
    save_output = input("Do you want to save the highlighted binary data to a file? (yes/no): ").strip().lower()
    if save_output == 'yes':
        base_file_path = input("Enter the base output file path (without extension): ").strip()
        
        # Saving with ANSI colors
        color_file_path = f"{base_file_path}_color.txt"
        try:
            with open(color_file_path, "w") as file:
                for pattern, highlighted in found_specific_patterns.items():
                    file.write(f"Pattern: {pattern}\n{highlighted}\n\n")
            print(f"Data with colors has been saved to {color_file_path}")
        except Exception as e:
            print(f"An error occurred while saving the color file: {e}")

        # Saving without ANSI colors
        no_color_file_path = f"{base_file_path}_nocolor.txt"
        try:
            with open(no_color_file_path, "w") as file:
                for pattern, highlighted in found_specific_patterns.items():
                    no_color_text = remove_ansi_codes(highlighted)
                    file.write(f"Pattern: {pattern}\n{no_color_text}\n\n")
            print(f"Data without colors has been saved to {no_color_file_path}")
        except Exception as e:
            print(f"An error occurred while saving the no-color file: {e}")
            

if __name__ == "__main__":
    main()
