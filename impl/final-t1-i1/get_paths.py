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

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--src_ip", default="10.0.1.10", help="local IP")
    parser.add_argument("--dst_ip", default="10.0.1.10", help="destination IP")
    parser.add_argument("--src_port", type=int, default=12348, help="Port to listen on")
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
    best_path = "-"
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
            
            if "best" in route_info_parsed:
                if removed:
                    best_path = "-"
                else:
                    best_path = as_path
    
        if paths == "-":
            return best_path + ":" + paths
        else:
            return best_path + ":" + paths[:-1]
    else:
        return "EMPTY"
    
if __name__ == '__main__':
    FLAGS = parse_flags()
    print "get_paths.py started"
    
    asn = ip_bgp_data.ip_to_asn(FLAGS.src_ip)
    if asn == "*":
        print "src_ip does not belong to an AS, exiting..."
        sys.exit(1)
    
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((FLAGS.src_ip, FLAGS.src_port))

    # receive requests
    while True:
        try:
            data, (ip, port) = server_socket.recvfrom(1024)
            
            if data:
                paths = get_as_paths(data)
                #logging.debug(asn + "-get_paths: " + str(paths))
                
                if paths != "EMPTY":
                    try:
                        server_socket.sendto(paths, (ip, port))
                    # if we can't reach the remote host, don't do anything
                    except IOError, e:
                        if e.errno == 101:
                            print ip + " is unreachable, skipping"
                        else:
                            raise
        except Exception as e:
            logging.error("\n" + asn + "-" + traceback.format_exc())

    server_socket.close()
