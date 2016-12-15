#!/usr/bin/python

import subprocess
import argparse
import time
import threading
import random

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--at", type=int, default=1)
    parser.add_argument("--peers", default=[["00/AS7018", "5100"], ["00/AS7018", "5200"], ["00/AS7018", "5300"], ["00/AS7018", "5400"], ["00/AS7018", "5500"], ["00/AS7018", "5600"]])
    parser.add_argument("--lists_folders", default="/home/marcus/ews/bgp")
    return parser.parse_args()

def send_from_peer_thread(updates_list, asn):
    router = asn + "_rt"
    dest = "20.0." + asn[:-2] + ".1"
    counter = 0
    at_float = float(int(FLAGS.at))
    
    asn_appended = asn + " " + asn
    asn_appends = {}    
    for x in range(1, 4):
        asn_appends[x] = {"append": asn_appended, "counter": 0}
    
    random.seed()

    print "starting..."
    while True:
        index = random.randint(0, (len(updates_list) - 1))
        updates = updates_list[index]
        if updates > 3:
            updates = 3
        
        process = None
        for x in range(1, updates + 1):
            process = subprocess.Popen(["sudo", "sh", "scripts/test_prepend.sh", router, str(x), ("\"" + asn_appends[x]["append"] + "\"")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        if updates >= 1:
            process.wait()
            process = subprocess.Popen(["sudo", "sh", "scripts/test_clear_out.sh", router, dest], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
        
        for x in range(1, updates + 1):
            asn_appends[x]["counter"] += 1
            if asn_appends[x]["counter"] > 4:
                asn_appends[x]["counter"] = 0
                asn_appends[x]["append"] = asn
            else:
                asn_appends[x]["append"] = asn_appends[x]["append"] + " " + asn
    
if __name__ == '__main__':
    FLAGS = parse_flags()
    print "send_from_peers.py started"
    at_str = "at-" + str(FLAGS.at)

    for peer in FLAGS.peers:
        list = peer[0]
        file_name = FLAGS.lists_folders + "/" + at_str + "/" + list
        updates_list = []
        
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                updates_list.append(line)
        
        print "list size of " + list + ": " + str(len(updates_list))
        random.seed()
        rand = random.uniform(0.100, 0.500)
        
        time.sleep(rand)
        threading.Thread(target=send_from_peer_thread, args=[updates_list, peer[1]]).start()
    