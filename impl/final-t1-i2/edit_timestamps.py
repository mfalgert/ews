import fileinput
import argparse
import os.path
import sys
from decimal import *

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--file_input", default="final-1/")
    return parser.parse_args()

# Modifies all config files in the specified folder to a new time value
def edit_timestamps(file_input):
    files = os.walk(".").next()[2]
    files_filtered = []
    for file in files:
        if file.startswith(file_input):
            files_filtered.append(file)
    files_filtered.sort()
    
    lowest = Decimal(str(float("inf")))
    lowest_file = "N/A"
    
    for result in files_filtered:
        with open(result) as f:
            for line in f:
                line_split = line.strip().split()
                
                if len(line_split) == 2:
                    timestamp = Decimal(line_split[0])
                    
                    if timestamp < lowest:
                        lowest = timestamp
                        lowest_file = result
    
    print "lowest timestamp is " + str(lowest) + ", found in file " + lowest_file
        
    for result in files_filtered:
        entries = 0
        for line in fileinput.input(result, inplace = 1):
            line_split = line.strip().split()
            
            if len(line_split) == 2:
                timestamp = Decimal(line_split[0])
                latency = Decimal(line_split[1])
                
                edited_timestamp = timestamp - lowest
                sys.stdout.write(str(edited_timestamp) + " " + str(latency) + "\n")
                entries += 1
                
        print "edited " + str(entries) + " entries in file \"" + result + "\""
        
if __name__ == '__main__':
    flags = parse_flags()
    print "editing result timestamps..."    
    edit_timestamps(flags.file_input)
