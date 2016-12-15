import fileinput
import argparse
import os.path
import sys

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--time", type=int, default=30)
    parser.add_argument("--folder", default="configs")
    parser.add_argument("--type", default="ebgp")
    return parser.parse_args()

# Modifies all config files in the specified folder to a new time value
def replace_timers():
    folders = os.walk(FLAGS.folder).next()[1]
    files = [FLAGS.folder + "/" + x + "/bgpd.conf" for x in folders]
    files.sort()
    
    for file in files:
        occurences = 0
        asn = ""
        current_asn = ""
        
        for line in fileinput.input(file, inplace = 1):
            line_split = line.split()
            if "router bgp" in line:
                asn = line_split[2]
                sys.stdout.write(line)
            elif "remote-as" in line:
                current_asn = line_split[3]
                sys.stdout.write(line)
            elif "advertisement-interval" in line and asn and current_asn and ((FLAGS.type == "ebgp" and asn != current_asn) or (FLAGS.type == "ibgp" and asn == current_asn)):
                sys.stdout.write(" " + " ".join(line_split[:-1]) + " " + str(FLAGS.time) + "\n")
                occurences += 1
            else:
                sys.stdout.write(line)
                
        print "replaced " + str(occurences) + " occurences in file \"" + file + "\""
        
if __name__ == '__main__':
    FLAGS = parse_flags()
    print "setting advertisement timers to " + str(FLAGS.time) + " secs..."   
    replace_timers()
