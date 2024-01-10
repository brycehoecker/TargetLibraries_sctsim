def read_registers(file_name):
    with open(file_name, 'r') as file:
        registers = [line.strip().split('. ') for line in file.readlines()]
    return {f'0x{int(num):x}': label for num, label in registers}

def color_text(text, color):
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "red": "\033[91m",
        "white": "\033[97m",
        "end": "\033[0m"
    }
    return f"{colors[color]}{text}{colors['end']}"

def display_bit_info(covered_bits):
    remaining_bits = {bit for bit in range(32)} - covered_bits
    covered_bits_str = ', '.join(str(bit) for bit in sorted(covered_bits, reverse=True))
    remaining_bits_str = ', '.join(str(bit) for bit in sorted(remaining_bits, reverse=True))
    print(color_text(f"Covered Bits: {{{covered_bits_str}}}.", "green"))
    print(color_text(f"Remaining Bits Needed: {{{remaining_bits_str}}}.", "red"))

def parse_bit_range(range_input):
    if '-' in range_input:
        start_bit, end_bit = map(int, range_input.split('-'))
    else:
        start_bit = end_bit = int(range_input)
    return start_bit, end_bit

def get_bit_range(reg_label, reg_num, covered_bits):
    print(color_text(f"You're entering information for Register {int(reg_num, 16)}, {reg_label}: Address {reg_num}", "blue"))
    display_bit_info(covered_bits)
    range_input = input(color_text("Enter the range of bits to define (e.g., 31-16, or a single bit like 11). : ", "white"))
    return parse_bit_range(range_input)

def get_bit_info():
    label = input("Enter the 'function' label for the bit(s): ")
    access_type = input("Are the bits Read-Only (R) or Read&Write (RW)? ")
    default_value = input("Enter the default value of the bit(s) (0 or 1): ")
    return label, access_type, default_value

def generate_cpp_structs(registers):
    cpp_code = ""
    for reg_num, reg_label in sorted(registers.items()):
        cpp_code += f"struct {reg_label} {{\n"
        covered_bits = set()
        while len(covered_bits) < 32:
            start_bit, end_bit = get_bit_range(reg_label, reg_num, covered_bits)
            label, access_type = get_bit_info()
            for bit in range(start_bit, end_bit - 1, -1):
                if bit not in covered_bits:
                    cpp_code += f"    // {label}\n"
                    if access_type.upper() == "RW":
                        cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
                        cpp_code += f"    void setBit{bit}(bool value) {{ /* Implement setter for bit {bit} */ }}\n"
                    elif access_type.upper() == "R":
                        cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
                    covered_bits.add(bit)
        cpp_code += "};\n\n"
    return cpp_code

def write_to_files(cpp_code, cpp_file, txt_file):
    with open(cpp_file, 'w') as file:
        file.write(cpp_code)
    with open(txt_file, 'w') as file:
        file.write(cpp_code)

def main():
    registers = read_registers("RegisterNames.txt")
    cpp_code = generate_cpp_structs(registers)
    write_to_files(cpp_code, "Registers.cpp", "Registers.txt")

if __name__ == "__main__":
    main()
