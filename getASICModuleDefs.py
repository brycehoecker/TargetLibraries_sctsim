import csv
from color_text_pkg.color_text import (
    red, green, blue, white, cyan
)

def display_bit_info(covered_bits):
    covered_bits_set = set(covered_bits)
    remaining_bits = sorted(set(range(32)) - covered_bits_set, reverse=True)
    covered_bits_str = ', '.join(str(bit) for bit in covered_bits_set)
    remaining_bits_str = ', '.join(str(bit) for bit in remaining_bits)
    print(green(f"Covered Bits: {{{{ {covered_bits_str} }}}}."))
    print(red(f"Remaining Bits Needed: {{{{ {remaining_bits_str} }}}}."))

def parse_bit_range(range_input):
    if '-' in range_input:
        start_bit, end_bit = map(int, range_input.split('-'))
    else:
        start_bit = end_bit = int(range_input)
    return start_bit, end_bit

def get_bit_range(reg_label, reg_num, covered_bits):
    print(cyan(f"You're entering information for Register {int(reg_num, 16)}, {reg_label}: Address {reg_num}"))
    covered_bits_list = list(covered_bits)  # Convert the set to a list
    covered_bits_list.sort(reverse=True)  # Sort the list in descending order
    display_bit_info(covered_bits_list)
    
    while len(covered_bits) < 32:
        bit_to_cover = input(white("Enter the bit to define (e.g., 31 for MSB, 0 for LSB): "))
        if bit_to_cover.isdigit() and 0 <= int(bit_to_cover) <= 31:
            bit_to_cover = int(bit_to_cover)
            if bit_to_cover in covered_bits:
                print(red("Bit already covered. Please enter a different bit."))
                continue
            covered_bits.add(bit_to_cover)
            label, access_type, default_value = get_bit_info()
            writer.writerow({'Register Number': reg_num, 'Register Label': reg_label, 'Bit Range': bit_to_cover, 'Function Label': label, 'Access Type': access_type, 'Default Value': default_value})
        else:
            print(red("Invalid input. Please enter a valid bit (0-31)."))
    return 0, 0  # Return dummy values since start_bit and end_bit are not used in this approach


def read_registers(file_name):
    with open(file_name, 'r') as file:
        registers = [line.strip().split('. ') for line in file.readlines()]
    return {f'0x{int(num):x}': label for num, label in registers}
    
def get_bit_info():
    label = input(white("Enter the 'function' label for the bit(s): "))
    access_type = input(white("Are the bits Read-Only (R) or Read&Write (RW)? "))
    default_value = input(white("Enter the default value of the bit(s) (0 or 1): "))
    return label, access_type, default_value

def save_to_csv(registers, filename):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Register Number', 'Register Label', 'Bit Range', 'Function Label', 'Access Type', 'Default Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for reg_num, reg_label in sorted(registers.items()):
            covered_bits = set()  # Initialize covered_bits here
            print(blue(f"Register {reg_num}, {reg_label}:"))
            while True:
                if len(covered_bits) >= 32:
                    break
                start_bit, end_bit = get_bit_range(reg_label, reg_num, covered_bits)
                for bit in range(start_bit, end_bit + 1):
                    covered_bits.add(bit)
                label, access_type, default_value = get_bit_info()
                bit_range = f"{start_bit}-{end_bit}" if start_bit != end_bit else f"{start_bit}"
                writer.writerow({'Register Number': reg_num, 'Register Label': reg_label, 'Bit Range': bit_range, 'Function Label': label, 'Access Type': access_type, 'Default Value': default_value})

def main():
    registers = read_registers("RegisterNames.txt")
    save_to_csv(registers, "register_data.csv")

if __name__ == "__main__":
    main()
