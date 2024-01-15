import os
import re
from graphviz import Digraph

def find_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                yield os.path.join(root, file)

def parse_includes(file_path):
    file_dir = os.path.dirname(file_path)
    includes = []
    with open(file_path, 'r') as file:
        for line in file:
            match = re.match(r'\s*#include\s*"(.+)"', line)
            if match:
                include_path = os.path.join(file_dir, match.group(1))
                include_path = os.path.normpath(include_path)  # Normalize the path
                includes.append(include_path)
    return includes

def build_include_tree(directory):
    include_tree = {}
    for file_path in find_files(directory, ('.cc', '.h')):
        absolute_path = os.path.abspath(file_path)
        includes = parse_includes(file_path)
        include_tree[absolute_path] = includes
    return include_tree

def display_tree(include_tree):
    dot = Digraph(comment='C++ Include Tree')
    for file, includes in include_tree.items():
        dot.node(file)
        for include in includes:
            dot.edge(file, include)
    dot.render('include_tree.gv', view=True)

directory = '/path/to/your/cpp/project'  # Replace with your directory path
include_tree = build_include_tree(directory)
display_tree(include_tree)
