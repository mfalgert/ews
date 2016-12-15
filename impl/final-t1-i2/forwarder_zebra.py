import subprocess
import argparse
import socket
import ip_bgp_data
import sys
import time
import calendar
import datetime
import logging
import traceback
import os
import inspect
from decimal import Decimal

self_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
logging.basicConfig(filename=self_path + "/logg.log", level=logging.DEBUG, format="%(asctime)s %(message)s")

def parse_FLAGS():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--src_ip", default="10.0.1.10", help="local IP")
    parser.add_argument("--prefixes", default=["10.0.13.0/24"], nargs="+")
    parser.add_argument("--logfile", default="/var/log/quagga/zebra.log", help="Logfile to be watched")
    parser.add_argument("--plotfile", default=self_path + "/results/", help="Plotfile to write to")
    return parser.parse_args()

def timestamp_to_unix_time(timestamp):
    time_split = timestamp.split(" ")
    time_1 = time_split[0].split("/")
    time_2 = time_split[1].split(":")
    
    year = int(time_1[0])
    month = int(time_1[1])
    day = int(time_1[2])
    hour = int(time_2[0])
    minute = int(time_2[1])
    
    seconds_split = time_2[2].split(".")
    second = int(seconds_split[0])
    msecond = int(seconds_split[1])

    dt = datetime.datetime(year, month, day, hour, minute, second)
    return Decimal(str(calendar.timegm(dt.timetuple())) + "." + str(msecond))

def write_to_file(file_name, timestamp_unix):
    file_append = open(file_name, "a")
    file_append.write(str(timestamp_unix) + "\n")
    file_append.flush()
    file_append.close()
    
def check_file_exists(file_name):
    if not os.path.isfile(file_name):
        file_create = open(file_name, "w")
        file_create.close()
    
if __name__ == '__main__':
    FLAGS = parse_FLAGS()
    print "forwarder_zebra.py started"
    
    asn = ip_bgp_data.ip_to_asn(FLAGS.src_ip)
    if asn == "*":
        print "src_ip does not belong to an AS, exiting..."
        sys.exit(1)
    
    # read from file continuously as new data is added
    process = subprocess.Popen(["tail", "-n", "0", "-F", FLAGS.logfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while True:
        # read logfile line, and get the relevant portion of it. example lines:
        # 2016/12/04 12:27:15.504 ZEBRA: netlink_route_multipath() (single hop): RTM_DELROUTE 10.0.5.0/24 type IPv4 nexthop
        
        try:
            line = process.stdout.readline().strip().split(" ZEBRA: ")
            
            if line and len(line) == 2:
                timestamp = line[0].strip()
                line_parsed = line[1].strip().split()

                if line_parsed[3] == "RTM_DELROUTE":
                    prefix = line_parsed[4]
                    
                    if prefix in FLAGS.prefixes:
                        #logging.debug(FLAGS.src_ip + "-" + asn + "-forwarder_zebra: " + str(prefix))
                        timestamp_unix = timestamp_to_unix_time(timestamp)
                        prefix_split = prefix.split("/")
                        prefix_ip = prefix_split[0]
                        
                        file_name = FLAGS.plotfile + FLAGS.src_ip + "-" + asn + "-" + prefix_ip + ".plot"
                        check_file_exists(file_name)
                        write_to_file(file_name, timestamp_unix)
        except Exception as e:
            logging.error("\n" + FLAGS.src_ip + "-" + asn + "-" + traceback.format_exc())

    forward_socket.close()
