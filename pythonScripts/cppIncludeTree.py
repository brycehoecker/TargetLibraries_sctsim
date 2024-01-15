import os
import re
from graphviz import Digraph
from collections import defaultdict

def find_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                yield file_path

def parse_includes(file_path, base_name_without_extension, file_extension):
    includes = []
    with open(file_path, 'r') as file:
        for line in file:
            # Match includes with angle brackets that contain the project-specific directory names
            match = re.match(r'\s*#include\s*["<](TargetDriver|targetio-pSCT|targetcalib-pSCT)/(.+\.(h|hh|cc|cpp))[">]', line)
            if match:
                # Construct the path from the matched groups
                include_path = os.path.join(match.group(1), match.group(2))
                include_file_name = os.path.splitext(os.path.basename(include_path))[0]
                # Avoid adding an include if it's a .h file with the same name as the .cc file
                if not (include_file_name == base_name_without_extension and file_extension != '.h'):
                    includes.append(include_file_name)
    return includes

def get_color_and_font(file_path):
    if 'targetdriver-pSCT' in file_path:
        return 'red', 'white'
    elif 'targetio-pSCT' in file_path:
        return 'blue', 'white'
    elif 'targetcalib-pSCT' in file_path:
        return 'green', 'black'
    else:
        return 'gray', 'black'

def build_include_tree(directory):
    include_tree = defaultdict(list)
    file_styles = {}
    all_files = set()

    # First pass to build the basic tree and assign styles
    for file_path in find_files(directory, ('.cc', '.h', '.cpp', '.hh')):
        file_name_without_extension, file_extension = os.path.splitext(os.path.basename(file_path))
        all_files.add(file_name_without_extension)
        file_color, font_color = get_color_and_font(file_path)
        file_styles[file_name_without_extension] = (file_color, font_color)
        direct_includes = parse_includes(file_path, file_name_without_extension, file_extension)
        for include in direct_includes:
            include_tree[file_name_without_extension].append(include)

    # Ensure all files are in the include_tree
    for file_name in all_files:
        if file_name not in include_tree:
            include_tree[file_name] = []

    return include_tree, file_styles

def display_tree(include_tree, file_styles):
    dot = Digraph(comment='C++ Include Tree')
    dot.attr('graph', rankdir='LR', ranksep='0.1', nodesep='0.1')
    dot.attr('node', shape='box')
    for file, includes in include_tree.items():
        color, fontcolor = file_styles.get(file, ('black', 'white'))
        dot.node(file, color=color, fontcolor=fontcolor, style='filled')
        for include in set(includes):
            if include in file_styles and include != file:  # Avoid self-loops
                dot.edge(file, include)
    dot.render('include_tree.gv', view=True)

directory = '/home/sctsim/git_repos/TargetLibraries_sctsim'
include_tree, file_styles = build_include_tree(directory)
display_tree(include_tree, file_styles)
