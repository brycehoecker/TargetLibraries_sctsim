import csv

def parse_bit_range(range_input):
    if '-' in range_input:
        start_bit, end_bit = map(int, range_input.split('-'))
    else:
        start_bit = end_bit = int(range_input)
    return start_bit, end_bit

def generate_cpp_structs_from_csv(file_name):
    cpp_code = ""
    with open(file_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        current_reg = None
        for row in reader:
            if current_reg != row['Register Label']:
                if current_reg is not None:
                    cpp_code += "};\n\n"
                current_reg = row['Register Label']
                cpp_code += f"struct {current_reg} {{\n"
            start_bit, end_bit = parse_bit_range(row['Bit Range'])
            for bit in range(start_bit, end_bit + 1):
                label = row['Function Label']
                access_type = row['Access Type'].upper()
                default_value = row['Default Value']
                cpp_code += f"    // {label}, default: {default_value}\n"
                if access_type == "RW":
                    cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
                    cpp_code += f"    void setBit{bit}(bool value) {{ /* Implement setter for bit {bit} */ }}\n"
                elif access_type == "R":
                    cpp_code += f"    bool getBit{bit}() const {{ /* Implement getter for bit {bit} */ }}\n"
        cpp_code += "};\n\n"
    return cpp_code

def main():
    cpp_code = generate_cpp_structs_from_csv("register_data.csv")
    with open("Registers.cpp", 'w') as file:
        file.write(cpp_code)

if __name__ == "__main__":
    main()
