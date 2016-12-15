# Traceroute functions/methods

import ip_bgp_data
import itertools

def parse_trace_line(trace_line):
    trace_line_parsed = " ".join(trace_line.split()).split()
    counter = 0
    
    for elem in trace_line_parsed:
        # this line contains a "*", meaning it timed out or the router did not respond
        if elem == "*":
            counter += 1
            if counter >= 3:
                return "*"

        # this line contains the time - skip this for now
        elif elem == "traceroute":
            return "N/A"

        # this line contains the ip
        elif len(elem.split(".")) == 4:
            ret_list = [elem]

            for entry in trace_line_parsed[1:]:
                if len(entry.split(".")) == 2:
                    ret_list.append(entry)
                    
            return ret_list[0] + "_" + ret_list[-1]

        # this line contains mpls - skip this, as we dont care
        elif elem == "MPLS":
            return "N/A"

    return "N/A"
        
def get_bgp_trace(trace):
    trace_split = trace.split('\n')[:-2] # remove trailing newlines
    
    last_asn = ip_bgp_data.local_asn
    last_latency = 0.0

    bgp_data = []
    bgp_trace = [last_asn]
    latency = 0.0
    
    # parse every line in the trace
    for trace_line in trace_split:
        hop = parse_trace_line(trace_line).split("_")
        
        if hop[0] == "N/A":
            continue
        else:
            asn = ip_bgp_data.ip_to_asn(hop[0])
            bgp_trace.append(asn)

            if asn != "*":
                latency = float(hop[1])
            
                if asn != last_asn and last_asn != "*":
                    bgp_data.append([last_asn, asn, latency - last_latency])
                    last_latency = latency

            last_asn = asn
    
    bgp_trace_filtered = [x[0] for x in itertools.groupby(bgp_trace)]
    bgp_trace_str = " ".join(bgp_trace_filtered)

    #if "*" in bgp_trace_str:
    #print bgp_trace_str + ": " + trace
    
    return [bgp_data, bgp_trace_str, latency]
