#!/usr/bin/env python
"""
    tokenize_python_source.py
    
    Accepts the path to a Python source file as input.
    Outputs the Python source file tokenized for use inline within a 
    CloudFormation template.
"""

from __future__ import print_function
import sys, os, json

def tokenize_python_source_file(source_path):
    
    lines_list = []
    with open(source_path, "r") as file_handle:
        for each_line in file_handle:
            lines_list.append(each_line.rstrip("\n"))
    
    return lines_list
        

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: {} path-to-python-source".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)
    
    source_path = sys.argv[1]
    
    if not os.path.isfile(source_path):
        print("File: {} not found.".format(source_path), file=sys.stderr)
    
    tokenized_source = tokenize_python_source_file(source_path)
    
    print(json.dumps(tokenized_source, indent=4))