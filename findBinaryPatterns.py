import re

# ANSI color codes
GREEN = '\033[92m'
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
    for match in re.finditer(regex_pattern, data):
        start, end = match.start(), match.end()
        highlighted_data += data[last_index:start]  # Before match
        # Highlight non-'x' parts of the pattern
        for i in range(start, end):
            if pattern[i - start] != 'x':
                highlighted_data += GREEN + data[i] + ENDC
            else:
                highlighted_data += data[i]
        last_index = end
    highlighted_data += data[last_index:]  # After last match

    # Function to calculate the visible length of the string (excluding ANSI codes)
    def visible_length(s):
        return len(re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', s))

    # Split the highlighted data into lines of specified length
    split_data = []
    line = ''
    for char in highlighted_data:
        line += char
        if visible_length(line) == line_length:
            split_data.append(line)
            line = ''
    # Add any remaining bits in the last line
    if line:
        split_data.append(line)

    return '\n'.join(split_data)

def find_specific_patterns(binary_data, patterns, line_length):
    found_patterns = {}
    for pattern in patterns:
        highlighted_data = highlight_matches(binary_data, pattern, line_length)
        if highlighted_data != binary_data:  # There was a match
            found_patterns[pattern] = highlighted_data
    return found_patterns

def main():
    file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir/packet_5640.bin"
    binary_data = read_binary_file_as_string(file_path)

    # User can specify the number of bits per line here
    bits_per_line = int(input("Enter the number of bits to display per line: "))

    print("Binary Data from File:")
    print('\n'.join([binary_data[i:i + bits_per_line] for i in range(0, len(binary_data), bits_per_line)]))

    specific_patterns = [
        "x000xxxxxxxxxxxxx001xxxxxxxxxxxxx010xxxxxxxxxxxxx011xxxxxxxxxxxx",
        "x000xxxxxxxxxxxxx001xxxxxxxxxxxxx010xxxxxxxxxxxxx011xxxxxxxxxxxxx100xxxxxxxxxxxxx101xxxxxxxxxxxxx110xxxxxxxxxxxxx111xxxxxxxxxxxx",
        # Add more patterns as needed
    ]

    found_specific_patterns = find_specific_patterns(binary_data, specific_patterns, bits_per_line)

    print("\nHighlighted Specific Patterns:")
    for pattern, highlighted in found_specific_patterns.items():
        print(f"Pattern: {pattern}\n{highlighted}\n")

if __name__ == "__main__":
    main()
