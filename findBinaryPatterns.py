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

def highlight_matches(data, pattern):
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
    return highlighted_data

def find_specific_patterns(binary_data, patterns):
    found_patterns = {}
    for pattern in patterns:
        highlighted_data = highlight_matches(binary_data, pattern)
        if highlighted_data != binary_data:  # There was a match
            found_patterns[pattern] = highlighted_data
    return found_patterns

def find_repeating_patterns(binary_data):
    found_patterns = {}
    for length in range(1, len(binary_data) // 2 + 1):
        for i in range(len(binary_data) - length):
            pattern = binary_data[i:i + length]
            if binary_data[i + length:i + 2 * length] == pattern:
                found_patterns[pattern] = found_patterns.get(pattern, 0) + 1
    return found_patterns

def main():
    file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir/packet_5640.bin"
    binary_data = read_binary_file_as_string(file_path)

    print("Binary Data from File:", binary_data)

    specific_patterns = [
        "x000xxxxxxxxxxxxx001xxxxxxxxxxxxx010xxxxxxxxxxxxx011xxxxxxxxxxxxx100xxxxxxxxxxxxx101xxxxxxxxxxxxx110xxxxxxxxxxxxx111xxxxxxxxxxxx",
        "x000xxxxxxxxxxxxx001xxxxxxxxxxxxx010xxxxxxxxxxxxx011xxxxxxxxxxxx"
        # Add more patterns as needed
    ]

    found_specific_patterns = find_specific_patterns(binary_data, specific_patterns)
    found_repeating_patterns = find_repeating_patterns(binary_data)

    print("\nHighlighted Specific Patterns:")
    for pattern, highlighted in found_specific_patterns.items():
        print(f"Pattern: {pattern}\n{highlighted}\n")
    
    print("Found Repeating Patterns:", found_repeating_patterns)

if __name__ == "__main__":
    main()












#file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir/packet_5640.bin"
#        "0000xxxxxxxxxxxx0001xxxxxxxxxxxx0010xxxxxxxxxxxx0011xxxxxxxxxxxx0100xxxxxxxxxxxx0101xxxxxxxxxxxx0110xxxxxxxxxxxx0111xxxxxxxxxxxx1000xxxxxxxxxxxx1001xxxxxxxxxxxx1010xxxxxxxxxxxx1011xxxxxxxxxxxx1100xxxxxxxxxxxx1101xxxxxxxxxxxx1110xxxxxxxxxxxx1111xxxxxxxxxxxx"

