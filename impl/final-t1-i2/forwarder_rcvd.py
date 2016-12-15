import subprocess
import argparse
import socket
import ip_bgp_data
import sys
import time
import logging
import traceback
import os
import inspect

self_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
logging.basicConfig(filename=self_path + "/logg.log", level=logging.DEBUG, format="%(asctime)s %(message)s")

def parse_FLAGS():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--src_ip", default="10.0.1.10", help="local IP")
    parser.add_argument("--dst_ip", default="10.0.1.10", help="IP to send to")
    parser.add_argument("--dst_port", type=int, default=12345, help="Port to send to")
    parser.add_argument("--prefixes", default=["10.0.13.0/24"], nargs="+")
    parser.add_argument("--logfile", default="/var/log/quagga/bgpd.log", help="Logfile to be watched")
    return parser.parse_args()

def get_as_paths(prefix):
    #BGP routing table entry for 10.0.26.0/24
    #Paths: (1 available, best #1, table Default-IP-Routing-Table)
      #Advertised to non peer-group peers:
      #20.0.5.1 20.0.9.1
      #2600
        #20.0.6.2 from 20.0.6.2 (10.0.26.10)
          #Origin IGP, metric 0, localpref 100, valid, external, best
          #Last update: Mon Jul 18 23:40:32 2016

    bgp_table_proc = subprocess.Popen("vtysh -c \"show ip bgp " + prefix + "\"", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, _ = bgp_table_proc.communicate()
    bgp_table_proc.wait()
    
    if "Network not in table" in stdout.strip():
        return "EMPTY"
    
    lines = stdout.split("\n")[3:-1]
    lines_trimmed = [x.strip() for x in lines]
    first_line_parsed = lines_trimmed[0].split()
    
    is_as_path = True
    for part in first_line_parsed:
        if not part.isdigit():
            is_as_path = False
            break
    
    if not is_as_path:
        lines_trimmed = lines_trimmed[1:]
        
    routes = [[]]
    for i, elem in enumerate(lines_trimmed):
        elem = elem.strip()
        
        if elem == "" and i != len(lines_trimmed) - 1:
            routes.append([])
        else:
            routes[-1].append(elem)

    paths = "-"
    if routes[0]:
        for route in routes:
            route_info = route[2]
            route_info_parsed = route_info.split(", ")
            
            if route[0] == "Local":
                as_path = asn
            else:
                as_path = asn + " " + route[0]
            
            removed = False
            if "removed" in as_path:
                removed = True
            if not removed:
                if paths == "-":
                    paths = ""
                paths += as_path + "!"
    
        if paths == "-":
            return paths
        else:
            return paths[:-1]
    else:
        return "EMPTY"
    
if __name__ == '__main__':
    FLAGS = parse_FLAGS()
    print "forwarder_rcvd.py started"
    
    asn = ip_bgp_data.ip_to_asn(FLAGS.src_ip)
    if asn == "*":
        print "src_ip does not belong to an AS, exiting..."
        sys.exit(1)
    
    # create socket for sending data to localhost
    forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # read from file continuously as new data is added
    process = subprocess.Popen(["tail", "-n", "0", "-F", FLAGS.logfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while True:
        # read logfile line, and get the relevant portion of it. example lines:
        # Announcement example: 2016/07/04 10:05:34.326 BGP: 20.0.3.2 rcvd UPDATE w/ attr: nexthop 20.0.3.2, origin i, path 900 1000 1100 1200 800
        #                       2016/07/04 10:05:34.326 BGP: 20.0.3.2 rcvd 10.0.8.0/24
        # Withdrawal example:   2016/07/04 10:48:05.088 BGP: 20.0.1.2 rcvd UPDATE about 10.0.3.0/24 -- withdrawn
        
        try:
            line = process.stdout.readline().strip().split(" BGP: ")
                
            if line and len(line) == 2:
                timestamp = line[0].strip()
                line_parsed = line[1].strip().split()
                src_asn = ip_bgp_data.ip_to_asn(line_parsed[0])
                
                if line_parsed[1] == "rcvd":
                    data = ""
                
                    if line_parsed[-1] == "withdrawn":
                        prefix = line_parsed[4]
                        if prefix not in FLAGS.prefixes:
                            continue
                        
                        time.sleep(0.001)
                        paths = get_as_paths(prefix)
                        #logging.debug(asn + "-forwarder_rcvd-withdrawn: " + str(paths))
                        
                        if paths != "EMPTY":
                            if src_asn == asn:
                                data = "IBGP_" + timestamp + "_" + prefix + "_withdrawn_" + asn + "_" + asn + " " + src_asn + "_" + FLAGS.src_ip + "_" + paths
                            else:
                                data = "EBGP_" + timestamp + "_" + prefix + "_withdrawn_" + asn + "_" + asn + " " + src_asn + "_" + FLAGS.src_ip + "_" + paths
                    elif "path" in line_parsed and "DENIED" not in line_parsed:        
                        path = " ".join(line[1].split(", ")[-1].split()[1:])
                        line = process.stdout.readline().strip().split(" BGP: ")
                            
                        if line and len(line) == 2:
                            timestamp = line[0].strip()
                            line_parsed = line[1].strip().split()
                        
                            if len(line_parsed) == 3:
                                prefix = line_parsed[2]
                                if prefix not in FLAGS.prefixes:
                                    continue
                                
                                time.sleep(0.001)
                                paths = get_as_paths(prefix)
                                #logging.debug(asn + "-forwarder_rcvd-announced: " + str(paths))
                                
                                if path and paths != "EMPTY":
                                    if src_asn == asn:
                                        data = "IBGP_" + timestamp + "_" + prefix + "_announced_" + asn + "_" + asn + " " + path + "_" + FLAGS.src_ip + "_" + paths
                                    else:
                                        data = "EBGP_" + timestamp + "_" + prefix + "_announced_" + asn + "_" + asn + " " + path + "_" + FLAGS.src_ip + "_" + paths
                
                    if data:
                        print data
                        try:
                            forward_socket.sendto(data, (FLAGS.dst_ip, FLAGS.dst_port))
                        except IOError, e:
                            if e.errno == 101:
                                print FLAGS.dst_ip + " is unreachable, skipping"
                                continue
                            else:
                                raise
        except Exception as e:
            logging.error("\n" + asn + "-" + traceback.format_exc())

    forward_socket.close()
