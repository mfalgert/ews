import socket
import threading
import argparse
import time
import subprocess
import tracerouting
import ip_bgp_data
import calendar
import datetime
import itertools
import random
import os.path
import copy
from decimal import Decimal
from sortedcontainers import SortedList

last_updates = {}
last_updates_local = {}
last_mappings = {}
last_decision = {}
last_converge = {}

prefix_ips = {}
asn_ips = {}
current_path = {}
previous_path = {}
path_decisions = {}
partial_latencies = {}
latency_history = {}

clients = []
router_paths = {}
router_cfg_temp = {}

def parse_flags():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--src_ip", default="10.0.1.10", help="IP to listen on")
    parser.add_argument("--forwarder_port", type=int, default=12345)
    parser.add_argument("--client_port", type=int, default=12346)
    parser.add_argument("--path_port_src", type=int, default=12347)
    parser.add_argument("--path_port_dst", type=int, default=12348)
    parser.add_argument("--dst_ips", nargs="+", default=["10.0.13.10"])
    parser.add_argument("--ews_ip", default="10.0.1.10")
    parser.add_argument("--routers", nargs="+", default=["20.0.1.1", "10.0.2.10", "20.0.3.1", "10.0.3.10", "20.0.4.1", "10.0.4.10", "20.0.5.1", "10.0.5.10", "20.0.6.1", "10.0.6.10", "20.0.7.1", "10.0.7.10", "20.0.8.1", 
    "10.0.8.10", "20.0.9.1", "10.0.9.10", "20.0.10.1", "10.0.10.10", "20.0.11.1", "10.0.11.10", "20.0.12.1", "10.0.12.10", "20.0.13.1", "10.0.13.10"])
    parser.add_argument("--ews_asn", default="100")
    parser.add_argument("--used_ases", nargs="+", default=["100", "200", "300", "400", "500", "600", "700", "800", "900", "1000", "1100", "1200", "1300"])
    parser.add_argument("--pass_time", default=30)
    parser.add_argument("--trace_interval", type=int, default=1, help="Seconds to sleep between traceroutes")
    
    return parser.parse_args()
    
def get_timestamp():
    now = datetime.datetime.now()
    return now.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

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
    
def seconds_to_hours(time):
    time_str = str(time)
    time_str_split = time_str.split(".")
    seconds = int(time_str_split[0])
    
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    return "%d:%02d:%02d" % (h, m, s)
 
def add_to_history(src_as, dst_as, as_lat):
    if src_as not in latency_history:
        latency_history[src_as] = {}
    if dst_as not in latency_history[src_as]:
        latency_history[src_as][dst_as] = SortedList(load=22)
    
    latency_history[src_as][dst_as].add(as_lat)
           
    if len(latency_history[src_as][dst_as]) >= 484:
        del latency_history[src_as][dst_as][0]
    
    if len(latency_history[src_as][dst_as]) % 2 == 0:
        partial_latencies[src_as][dst_as] = latency_history[src_as][dst_as][(len(latency_history[src_as][dst_as]) / 2) - 1]
    else:
        partial_latencies[src_as][dst_as] = latency_history[src_as][dst_as][((len(latency_history[src_as][dst_as]) - 1) / 2)]

def investigate_new_path(new_path_split, prev_path_split, prev_ts, common_asn, common_ases, updates_received, convergence_start):
    paths_diverged = False
    new_ts = prev_ts
    new_ases = list(common_ases)
    new_path = " ".join(new_path_split)
    new_early_updates = {}

    for i, asn in enumerate(new_path_split[:-1]):
        if not paths_diverged:
            new_ases.append(asn)
            if asn == prev_path_split[i]:
                common_asn = i
                common_ases.append(asn)
            else:
                paths_diverged = True
    
        if asn not in FLAGS.used_ases:
            continue
        
        updates_list = updates_received[asn]     
        for entry in updates_list:
            if entry["path"] in new_path:
                if entry["timestamp"] >= convergence_start and new_ts >= entry["timestamp"]:
                    if entry["action"] == "announced":
                        if asn not in new_early_updates:
                            new_early_updates[asn] = {}
                            
                        new_ases_copy = list(new_ases)
                        new_early_updates[asn] = {"update": entry, "ases": new_ases_copy}
                        
                        new_ts = entry["timestamp"]
                        if not paths_diverged:
                            prev_ts = new_ts
                            
                        break
    
    return {"common_asn": common_asn, "common_ases": common_ases, "prev_ts": prev_ts, "early_updates": new_early_updates}
            
def learning_process(prefix, convergence_start, router_paths_cfg, curr_path, prev_path, updates_received):
    # Infer if update caused path to change or not
    convergence_start -= 3
    
    print "prev / curr - " + str(prev_path) + " / " + str(curr_path)
    #print "convergence started at " + str(convergence_start)
    if prev_path != curr_path:
        # find early updates
        early_updates = {}
        final_update = {}
        
        for update in updates_received[FLAGS.ews_asn]:
            if update["timestamp"] >= convergence_start:
                path_filtered = " ".join([x[0] for x in itertools.groupby(update["path"].split())])
                if (update["action"] == "announced" and path_filtered == curr_path) or (update["action"] == "withdrawn" and path_filtered in prev_path):
                    print "final update: " + str(path_filtered)
                    final_update = copy.deepcopy(update)
                    break
        
        if final_update:
            prev_path_split = prev_path.split()
            prev_ts = final_update["timestamp"]
            common_asn = -1
            common_ases = []
            
            if final_update["action"] == "announced":
                new_path_split = [x[0] for x in itertools.groupby(final_update["path"].split())]
                data = investigate_new_path(new_path_split, prev_path_split, prev_ts, common_asn, common_ases, updates_received, convergence_start)
                common_asn = data["common_asn"]
                common_ases = data["common_ases"]
                prev_ts = data["prev_ts"]
                new_early_updates = data["early_updates"]
                
                for key, value in new_early_updates.iteritems():
                    early_updates[key] = value
                            
            for i, asn in enumerate(prev_path_split[:-1]):
                if common_asn >= i or asn not in FLAGS.used_ases:
                    continue
                
                updates_list = updates_received[asn]    
                for entry in updates_list:
                    if entry["path"] in prev_path:
                        if entry["timestamp"] >= convergence_start and entry["timestamp"] <= prev_ts:
                            common_asn = i
                            common_ases.append(asn)
                            
                            if asn not in early_updates:
                                early_updates[asn] = {}
                                
                            common_ases_copy = list(common_ases)
                            early_updates[asn] = {"update": entry, "ases": common_ases_copy}
                            prev_ts = entry["timestamp"]
                            
                            if entry["action"] == "announced":
                                new_path_split = entry["path"].split()
                                
                                if len(new_path_split) > 1:
                                    data = investigate_new_path(new_path_split, prev_path_split, prev_ts, common_asn, common_ases, updates_received, convergence_start)
                                    common_asn = data["common_asn"]
                                    common_ases = data["common_ases"]
                                    prev_ts = data["prev_ts"]
                            
                            break
            
            # infer how long previous mappings lasted for
            if last_mappings[prefix]:
                for mapping_entry in last_mappings[prefix]:
                    mapping = path_decisions[prefix][mapping_entry["asn"]][mapping_entry["action"]][mapping_entry["path"]][mapping_entry["configs"]]
                    duration = final_update["timestamp"] - mapping["timestamp"]
                    duration_str = seconds_to_hours(duration)
                    path_decisions[prefix][mapping_entry["asn"]][mapping_entry["action"]][mapping_entry["path"]][mapping_entry["configs"]]["duration"] = duration_str
                
                last_mappings[prefix] = []
            
            if early_updates:
                for asn, updt in early_updates.iteritems():
                    configs = ""
                    for asn_entry in updt["ases"]:
                        configs += asn_entry + "/"
                        for ip, dicts in router_paths_cfg[asn_entry].iteritems():
                            configs += ip + ";" + dicts["available_paths"] + ":"
                        configs = configs[:-1]
                        configs += "|"
                    configs = configs[:-1]
                    
                    if asn not in path_decisions[prefix]:
                        path_decisions[prefix][asn] = {}
                    
                    update = updt["update"]
                    if update["action"] not in path_decisions[prefix][asn]:
                        path_decisions[prefix][asn][update["action"]] = {}
                    if update["path"] not in path_decisions[prefix][asn][update["action"]]:
                        path_decisions[prefix][asn][update["action"]][update["path"]] = {}
                    
                    path_decisions[prefix][asn][update["action"]][update["path"]][configs] = {"path": curr_path, "timestamp": final_update["timestamp"], "duration": "Unknown"}
                    
                    mapping_entry = {"asn": asn, "action": update["action"], "path": update["path"], "configs": configs}
                    last_mappings[prefix].append(mapping_entry)
                    #print "mapping: " + str(mapping_entry)
        else:
            for update in updates_received[ip_bgp_data.local_asn]:
                path_filtered = " ".join([x[0] for x in itertools.groupby(update["path"].split())])
                print "update: " + str(path_filtered)
                    
def check_converge():
    for prefix in last_converge.iterkeys():
        if not last_converge[prefix]["converged"]:
            local_timestamp = timestamp_to_unix_time(get_timestamp())
            if local_timestamp > last_converge[prefix]["timestamp"] + FLAGS.pass_time:
                get_current_path(prefix)
                print "convergence ended for " + prefix
                threading.Thread(target=learning_process, args=[prefix, last_converge[prefix]["started"], copy.deepcopy(router_cfg_temp[prefix]), 
                current_path[prefix], previous_path[prefix], last_updates[prefix]]).start()
                last_converge[prefix]["converged"] = True

def wait_for_traceroutes(processes):
    # wait for all processes to finish
    for (dst, proc, pipe) in processes:
        proc.wait()
        stdout, _ = pipe
        trace_timestamp = timestamp_to_unix_time(get_timestamp())

        trace_data = tracerouting.get_bgp_trace(stdout)
        bgp_data = trace_data[0]
        bgp_trace_str = trace_data[1]
        bgp_trace_latency = trace_data[2]

        if bgp_trace_latency != 0.0:
            for elem in bgp_data:
                if elem[0] not in partial_latencies:
                    partial_latencies[elem[0]] = {}
                if elem[1] not in partial_latencies:
                    partial_latencies[elem[1]] = {}
                
                threading.Thread(target=add_to_history, args=[elem[0], elem[1], elem[2]]).start()
 
def traceroute_thread():
    traces = 0
    while True:
        processes = []
        for dst_ip in FLAGS.dst_ips:
            process = subprocess.Popen(["sudo", "paris-traceroute", "-T", "500", "-w", "100", "-n", "-M", "3", "-p", "udp", dst_ip],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append((dst_ip, process, process.communicate()))
        
        wait_for_traceroutes(processes)
        threading.Thread(target=check_converge).start()
        traces += 1
        #print traces
        
        random.seed()
        rand = random.uniform(0.010, 0.050)
        time.sleep(rand)

def get_lowest_latency_path(start, end):
    # disjktra's algorithm
    distances = {}
    predecessors = {}
    to_assess = partial_latencies.keys()

    for node in partial_latencies:
        distances[node] = float("inf")
        predecessors[node] = None

    sp_set = []
    distances[start] = 0

    while len(sp_set) < len(to_assess):
        still_in = {node: distances[node] for node in [node for node in to_assess if node not in sp_set]}
        closest = min(still_in, key = distances.get)
        sp_set.append(closest)

        for node in partial_latencies[closest]:
            if distances[node] > distances[closest] + partial_latencies[closest][node]:
                distances[node] = distances[closest] + partial_latencies[closest][node]
                predecessors[node] = closest

    path = [end]
    while start not in path:
        path.append(predecessors[path[-1]])
        
    path_ordered = path[::-1]
    path_latency = distances[end]

    return {"path": path_ordered, "latency": path_latency}
            
def get_path_latency(path):
    path_filtered = [x[0] for x in itertools.groupby(path)]
    latency = 0.0
    
    for i, _ in enumerate(path_filtered[:-1]):
        if path_filtered[i] in partial_latencies and path_filtered[i+1] in partial_latencies[path_filtered[i]]:
            latency += partial_latencies[path_filtered[i]][path_filtered[i+1]]
        else:
            return 0.0
    
    return latency

def check_config(key, router_cfg):
    saved_configs = key.split("|")
    for config in saved_configs:
        split_config = config.split("/")
        
        asn = split_config[0]
        entries = split_config[1].split(":")
        
        for entry in entries:
            entry_split = entry.split(";")
            ip = entry_split[0]
            cfg = entry_split[1] 
        
            #print "saved config (" + str(ip) + "): " + str(cfg)
            #print "router config (" + str(ip) + "): " + str(router_cfg[asn][ip]["available_paths"])
            
            if router_cfg[asn][ip]["available_paths"] != cfg:
                return False
    
    return True
    
def check_if_match_exists(router_cfg, prefix, asn, action, path):
    if prefix in path_decisions:
        if asn in path_decisions[prefix]:
            if action in path_decisions[prefix][asn]:
                if path in path_decisions[prefix][asn][action]:
                    for key, value in path_decisions[prefix][asn][action][path].iteritems():
                        #print "CHECKING: " + key
                        if check_config(key, router_cfg):
                            return value

    return None

def decision_process(router_cfg, prefix, asn, action, path):
    decision = None
    # find best match
    mapping = check_if_match_exists(router_cfg, prefix, asn, action, path)
    
    if mapping:
        new_path = mapping["path"]
        duration = mapping["duration"]
        
        # found a match
        if new_path != last_decision[prefix]:
            current_path_latency = get_path_latency(current_path[prefix].split())
            new_path_latency = get_path_latency(new_path.split())

            if current_path_latency != 0.0 and new_path_latency != 0.0:
                # run dijkstra's algorithm between source and destination AS to find lowest latency path
                ases = current_path[prefix].split()
                lowest_latency_path = get_lowest_latency_path(ases[0], ases[-1])

                # get current latencies
                current_latency_order = []
                prefix_index = 0
                for i, asn_prefix in enumerate(last_decision.iterkeys()):
                    prefix_latency = get_path_latency(current_path[asn_prefix].split())
                    current_latency_order.append([asn_prefix, prefix_latency])

                    if asn_prefix == prefix:
                        prefix_index = i

                # insert the new latency in a copy of the list of latencies
                new_latency_order = copy.deepcopy(current_latency_order)
                new_latency_order[prefix_index][1] = new_path_latency

                # sort both lists by latency
                current_latency_order.sort(key=lambda x: x[1])
                new_latency_order.sort(key=lambda x: x[1])

                # insert ordering numbers and turn them into strings
                current_latency_order_str = ""
                new_latency_order_str = ""
                for i, _ in enumerate(current_latency_order):
                    current_latency_order_str += str(i + 1) + ". " + str(current_latency_order[i][0]) + " [" + str(current_latency_order[i][1]) + " ms], "
                    new_latency_order_str += str(i + 1) + ". " + str(new_latency_order[i][0]) + " [" + str(new_latency_order[i][1]) + " ms], "

                current_latency_order_str = current_latency_order_str[:-2]
                new_latency_order_str = new_latency_order_str[:-2]

                # create the full strings to be sent to the clients
                print "Update " + action + " / " + path + " - EARLY WARNING PRODUCED"
                decision = "---( [" + prefix + "] )---" + \
                "\n - Current latency: " + str(current_path_latency) + \
                "\n - New latency: " + str(new_path_latency) + \
                "\n - Previous new path duration: " + duration + \
                "\n - Lowest latency path: " + " ".join(lowest_latency_path["path"]) + " [" + str(lowest_latency_path["latency"]) + " ms]" + \
                "\n - Current replica ordering: " + str(current_latency_order_str) + \
                "\n - New replica ordering: " + str(new_latency_order_str)
            else:
                print "Update " + action + " / " + path + " - NO LATENCY DATA (" + str(current_path_latency) + " / " + str(new_path_latency) + ")"
        else:
            print "Update " + action + " / " + path + " - IDENTICAL WARNING ALREADY SENT"
    else:
        print "Update " + action + " / " + path + " - NO ENTRY"

    # if best match found, notify clients
    if decision:
        print decision
        last_decision[prefix] = new_path

        for ip in clients:
            message = "UPDATE_" + decision
            upstream_socket.sendto(message, (ip, FLAGS.client_port))

def get_current_path(prefix):
    # ask local BGP router about current path
    paths_socket.sendto(prefix, (FLAGS.ews_ip, FLAGS.path_port_dst))
    # get response
    config, addr = paths_socket.recvfrom(1024)
    
    if config != "EMPTY":
        best_path = config.split(":")[0]
        current_path[prefix] = best_path
    
    print "current path installed: " + current_path[prefix]
            
def install_all_paths(prefix, config, ip):
    if config != "EMPTY":
        asn = ip_bgp_data.ip_to_asn(ip)
    
        paths = config.split(":")
        router_paths[prefix][asn][ip]["best_path"] = paths[0]
        
        if asn == ip_bgp_data.local_asn:
            current_path[prefix] = paths[0]
        
        available_paths_list = []
        available_paths = paths[1].split("!")
        
        for i, path in enumerate(available_paths):
            available_paths_list.append(path)

        available_paths_list.sort()
        router_paths[prefix][asn][ip]["available_paths"] = "!".join(available_paths_list)
    else:
        router_paths[prefix][asn][ip]["best_path"] = "-"
        router_paths[prefix][asn][ip]["available_paths"] = "-"
        
def install_available_paths(prefix, config, ip):
    if config != "EMPTY":
        asn = ip_bgp_data.ip_to_asn(ip)
    
        available_paths_list = []
        available_paths = config.split("!")

        for i, path in enumerate(available_paths):
            available_paths_list.append(path)

        available_paths_list.sort()
        router_paths[prefix][asn][ip]["available_paths"] = "!".join(available_paths_list)
    else:
        router_paths[prefix][asn][ip]["available_paths"] = "-"
        
def upstreams_thread():
    while True:
        upstream_data, _ = upstream_socket.recvfrom(1024)
        data_parsed = upstream_data.split("_")
        
        type = data_parsed[0].strip()
        timestamp = timestamp_to_unix_time(data_parsed[1].strip())
        prefix = data_parsed[2].strip()
        action = data_parsed[3].strip()
        asn = data_parsed[4].strip()
        path = data_parsed[5].strip()
        ip = data_parsed[6].strip()
        config = data_parsed[7].strip()
       
        if prefix in last_decision:
            #print data_parsed
            
            if type == "EBGP":
                if last_converge[prefix]["converged"]:
                    last_converge[prefix]["timestamp"] = timestamp
                    last_converge[prefix]["converged"] = False
                    last_converge[prefix]["started"] = timestamp
                    previous_path[prefix] = current_path[prefix]
                    router_cfg_temp[prefix] = copy.deepcopy(router_paths[prefix])
                    print "convergence started for " + prefix
                else:
                    last_converge[prefix]["timestamp"] = timestamp
            
                # add update to history
                if prefix in last_updates and asn in last_updates[prefix]:
                    update_dict = {"timestamp": timestamp, "action": action, "path": path}
                    
                    if "*" not in path:
                        last_updates[prefix][asn].insert(0, update_dict)
                        
                        if len(last_updates[prefix][asn]) > 20:
                            last_updates[prefix][asn].pop()
                    
                    # check if mapping exists
                    threading.Thread(target=decision_process, args=[copy.deepcopy(router_paths[prefix]), prefix, asn, action, path]).start()
                
            install_available_paths(prefix, config, ip)
    
def clients_thread():
    while True:
        client_data, (client, client_port) = client_socket.recvfrom(1024)
        response = "PROTO_Request invalid"

        # interface for registering/unregistering clients
        if client_data == "register" and client not in clients:
            clients.append(client)
            response = "PROTO_Joined server"
            print "Client " + client + " joined"
        elif client_data == "unregister" and client in clients:
            clients.remove(client)
            response = "PROTO_Left server"
            print "Client " + client + " left"

        client_socket.sendto(response, (client, FLAGS.client_port))
        
def infer_paths(prefix, ip):
    # ask AS routers for available paths/peers
    paths_socket.sendto(prefix, (ip, FLAGS.path_port_dst))
    # get response
    config, addr = paths_socket.recvfrom(1024)
    install_all_paths(prefix, config, ip)
    print "installed path(s) for " + ip

if __name__ == "__main__":
    FLAGS = parse_flags()
    print "ews_server.py started"
 
    # set local as and local ip
    ip_bgp_data.set_local_ip_asn(FLAGS.src_ip)

    # add destination prefixes
    for dst_ip in FLAGS.dst_ips:
        prefix = ip_bgp_data.ip_to_prefix(dst_ip)
    
        last_decision[prefix] = "-"
        last_mappings[prefix] = []
        last_converge[prefix] = {"timestamp": 0.0, "converged": True, "started": 0.0}
        current_path[prefix] = "-"
        previous_path[prefix] = "-"
        last_updates[prefix] = {}
        last_updates_local[prefix] = {}
        path_decisions[prefix] = {}
        
        if prefix not in router_paths:
            router_paths[prefix] = {}
        
        for asn in FLAGS.used_ases:    
            last_updates[prefix][asn] = []
            last_updates_local[prefix][asn] = []
            
        for ip in FLAGS.routers:
            asn = ip_bgp_data.ip_to_asn(ip)
            
            if asn not in router_paths[prefix]:
                router_paths[prefix][asn] = {}
                
            router_paths[prefix][asn][ip] = {"best_path": "-", "available_paths": "-"}

        print "added prefix \"" + prefix + "\"" 

    # initialize sockets
    upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    upstream_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    upstream_socket.bind((FLAGS.src_ip, FLAGS.forwarder_port))
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((FLAGS.src_ip, FLAGS.client_port))
    
    paths_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    paths_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    paths_socket.bind((FLAGS.src_ip, FLAGS.path_port_src))
    
    # initialize current path data
    for prefix in last_decision.iterkeys():
        for router_ip in FLAGS.routers:
            infer_paths(prefix, router_ip)
        get_current_path(prefix)
    router_cfg_temp = copy.deepcopy(router_paths)

    # start threads
    threading.Thread(target=upstreams_thread).start()
    threading.Thread(target=clients_thread).start()
    threading.Thread(target=traceroute_thread).start()
