from color_text_pkg.color_text import (
    red, green, blue, yellow, black, magenta, cyan, white,
    b_red, b_green, b_blue, b_yellow, b_black, b_magenta, b_cyan, b_white
)

# Function to print the color name in its corresponding color
def display_color(color_func, text):
    print(color_func(text))

# Standard colors
print("Standard colors:")
display_color(black, "black")
display_color(red, "red")
display_color(green, "green")
display_color(yellow, "yellow")
display_color(blue, "blue")
display_color(magenta, "magenta")
display_color(cyan, "cyan")
display_color(white, "white")

# Bright colors
print("\nBright colors:")
display_color(b_black, "b_black")
display_color(b_red, "b_red")
display_color(b_green, "b_green")
display_color(b_yellow, "b_yellow")
display_color(b_blue, "b_blue")
display_color(b_magenta, "b_magenta")
display_color(b_cyan, "b_cyan")
display_color(b_white, "b_white")
