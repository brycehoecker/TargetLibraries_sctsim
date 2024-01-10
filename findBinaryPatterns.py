import re

def read_binary_file_as_string(file_path):
    with open(file_path, "r") as file:
        binary_data = file.read().strip()
    return binary_data

def pattern_to_regex(pattern):
    return pattern.replace('x', '.')

def find_specific_patterns(binary_data, patterns):
    found_patterns = {}
    for pattern in patterns:
        regex_pattern = pattern_to_regex(pattern)
        matches = re.findall(regex_pattern, binary_data)
        if matches:
            found_patterns[pattern] = matches
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
    ]

    found_specific_patterns = find_specific_patterns(binary_data, specific_patterns)
    found_repeating_patterns = find_repeating_patterns(binary_data)

    print("Found Specific Patterns:", found_specific_patterns)
    print("Found Repeating Patterns:", found_repeating_patterns)

if __name__ == "__main__":
    main()













#file_path = "/home/sctsim/copied_from_wipac/copy_folder/already_extracted_files/Module12345/wiresharkToBinaryOutputDir/packet_5640.bin"
#        "0000xxxxxxxxxxxx0001xxxxxxxxxxxx0010xxxxxxxxxxxx0011xxxxxxxxxxxx0100xxxxxxxxxxxx0101xxxxxxxxxxxx0110xxxxxxxxxxxx0111xxxxxxxxxxxx1000xxxxxxxxxxxx1001xxxxxxxxxxxx1010xxxxxxxxxxxx1011xxxxxxxxxxxx1100xxxxxxxxxxxx1101xxxxxxxxxxxx1110xxxxxxxxxxxx1111xxxxxxxxxxxx"
