def read_registers(file_name):
    with open(file_name, 'r') as file:
        registers = [line.strip().split('. ') for line in file.readlines()]
    return {int(num): label for num, label in registers}

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
    print(color_text(f"You're entering information for Register {reg_num}, {reg_label}: Address 0x{reg_num:x}", "blue"))
    display_bit_info(covered_bits)
    range_input = input(color_text("Enter the range of bits to define (e.g., 31-16, or a single bit like 11). : ", "white"))
    return parse_bit_range(range_input)

def get_bit_info():
    label = input("Enter the function definition/label for the bit(s): ")
    access_type = input("Are the bits Read-Only (RO) or Read&Write (RW)? ")
    default_value = input("Enter the default value of the bit(s) (0 or 1): ")
    return label, access_type, default_value

def get_predefined_bit_info(reg_num):
    predefined_info = {
        0: {31: ("Assigned value of 0xFED000030, assigned in Firmware to highlight and track incremental changes in firmware. Incremented with every firmware revision", "RO", "0")},
        1: {
            31: ("Any value for control software, does not have effect on any FPGA logic", "RW", "0"),
            15: ("Detector ID, fill Detector ID field of reported event", "RW", "0"),
            7: ("CTA ID, fill CTA ID field of reported event", "RW", "0"),
        },
        2: {31: ("Serial number the least significant word", "RO", "0")},
        3: {31: ("Serial number the most significant word", "RO", "0")},
        4: {
            31: ("Unused, always 0", "R", "0"),
            15: ("Status of backplane lines from bp4 to bp7 (also, bp5 is reset and will not be available due to board reset)", "R", "0"),
            11: ("Unused, always 0", "R", "0"),
            10: ("mgt_AVCC_OK is OK, 1- OK, 0 – is not", "R", "0"),
            9: ("+1_8V is OK, 1- OK, 0 – is not", "R", "0"),
            8: ("Unused, always 0", "R", "0"),
            1: ("Underflow on summary FIFO of event data", "R", "0"),
            0: ("overflow on summary FIFO of event data", "R", "0"),
        }
    }
    return predefined_info[reg_num]

def generate_cpp_structs(registers):
    cpp_code = ""
    for reg_num, reg_label in sorted(registers.items()):
        if reg_num in [0, 1, 2, 3, 4]:  # Predefined registers
            cpp_code += f"struct {reg_label} {{\n"
            predefined_info = get_predefined_bit_info(reg_num)
            for bit in range(31, -1, -1):
                if bit in predefined_info:
                    label, access_type, default_value = predefined_info[bit]
                    cpp_code += f"    // {label}\n"
                    if access_type == "RW":
                        cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
                        cpp_code += f"    void setBit{bit}(bool value) {{ /* Implement setter for bit {bit} */ }}\n"
                    elif access_type == "RO":
                        cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
            cpp_code += "};\n\n"
        else:
            # Handle other registers if necessary
            pass
    return cpp_code

def write_to_files(cpp_code, cpp_file, txt_file):
    with open(cpp_file, 'w') as file:
        file.write(cpp_code)
    with open(txt_file, 'w') as file:
        file.write(cpp_code)

def main():
    registers = read_registers("RegisterNames.txt")
    cpp_structs = generate_cpp_structs(registers)
    write_to_files(cpp_structs, "Registers.cpp", "Registers.txt")

if __name__ == "__main__":
    main()
