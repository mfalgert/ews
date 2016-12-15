#!/usr/bin/env python

import os, time, calendar
import argparse
from dpkt import bgp
from pybgpdump import BGPDump
import dumbnet as dnet
import datetime as dtime
import numpy as np
from netaddr import IPNetwork, IPAddress

updates = []        # updates who passes the filter
plots = []          # timestamps of such updates are saved here
filters = []        # specified filters

start_date_unix = 0 # start of interval in unix-time
end_date_unix = 0   # end of interval in unix-time
dates_unix = []     # if any specific dates are used, save them here for future use
origin = []

ip_freq = {}
ip_long = {}
ip_short = {}
intervals = {}

def empty_update():
    BGP_FIELDS = ({'origin':'', 'as_path':[], 'next_hop':'', 'multi_exit_disc':'', 'local_pref':'',
                        'atomic_aggregate':'', 'aggregator_as':'', 'aggregator_ip':'', 'originator_id':'',
                        'cluster_list':[], 'communities':[], 'date':'', 'from_ip':'', 'from_as':'',
                        'to_ip':'', 'to_as':'', 'announced':[], 'withdrawn':[]})
    return BGP_FIELDS

# parses as path to array of strings
def aspath_to_array(as_path):
    str = ''
    for seg in as_path.segments:
        if seg.type == bgp.AS_SET:
            start = '['
            end = '] '
        elif seg.type == bgp.AS_SEQUENCE:
            start = ''
            end = ' '
        else:
            start = '?%d?' % seg.type
            end = '? '
        str += start
        for AS in seg.path:
            str += '%d ' % AS
        str = str[:-1]
        str += end
    str = str[:-1]
    arr = str.split()
    return arr

# parses origin to string
def origin_to_str(origin):
    str = ''
    if origin.type == bgp.ORIGIN_IGP:
        str = 'IGP'
    elif origin.type == bgp.ORIGIN_EGP:
        str = 'EGP'
    elif origin.type == bgp.INCOMPLETE:
        str = 'INCOMPLETE'
    return str

# parses communities to array of strings
def communities_to_array(communities):
    arr = []
    for i, comm in enumerate(communities.list, start=0):
        arr.append('')
        try:
            arr[i] = '%d:%d' % (comm.asn, comm.value)
        except AttributeError:
            arr[i] = '%d' % comm.value
    return arr

# parses clusterlist to array of strings
def clusterlist_to_array(cluster_list):
    arr = []
    for i, cluster in enumerate(cluster_list.list, start=0):
        arr.append('')
        arr[i] = dnet.ip_ntoa(cluster)
    return arr

# parses announced or withdrawn to array of routes
def announced_or_withdrawn_to_array(routes):
    arr = []
    for i, route in enumerate(routes, start=0):
        arr.append('')
        arr[i] = '%s/%d' % (dnet.ip_ntoa(route.prefix), route.len)
    return arr

# dates in BGP updates must be parsed according to their specific convention
def update_date_to_unix_timestamp(date):
    date_and_time = date.split()

    date_arr = date_and_time[0].split('/')
    year = int('20%s' % date_arr[2])
    month = int(date_arr[0])
    day = int(date_arr[1])

    time_arr = date_and_time[1].split(':')
    hour = int(time_arr[0])
    min = int(time_arr[1])
    sec = int(time_arr[2])

    dt = dtime.datetime(year, month, day, hour, min, sec)
    unix_timestamp = calendar.timegm(dt.timetuple())
    return unix_timestamp

# converts a "date-array (yy.mm.dd.hh.mm.ss)" to unix-time
def array_to_unix_timestamp(arr):
    diff = 6 - len(arr)
    if diff > 0:
        while (len(arr) < 6):
            arr.append(0)

    year = int(arr[0])
    month = int(arr[1])
    day = int(arr[2])
    hour = int(arr[3])
    min = int(arr[4])
    sec = int(arr[5])

    dt = dtime.datetime(year, month, day, hour, min, sec)
    unix_timestamp = calendar.timegm(dt.timetuple())
    return unix_timestamp

# converts from yy-format to yyyy-format
def format_year(year):
    if len(year) == 2:
        year = '20%s' % year
    return year

# prints BGP updates in a nice format
def print_update(update):
    if FLAGS.print_updates == 1:
        print 'DATE: %s' % update['date']
        print 'TYPE: BGP4MP/MESSAGE/Update'
        print 'FROM: %s AS%d' % (update['from_ip'], update['from_as'])
        print 'TO: %s AS%d' % (update['to_ip'],  update['to_as'])
        if update['origin']:
            print 'ORIGIN: %s' % update['origin']
        if update['as_path']:
            print 'AS_PATH: %s' % ' '.join(update['as_path'])
        if update['next_hop']:
            print 'NEXT_HOP: %s' % update['next_hop']
        if update['multi_exit_disc']:
            print 'MULTI_EXIT_DISC: %s' % update['multi_exit_disc']
        if update['local_pref']:
            print 'LOCAL_PREF: %s' %  update['local_pref']
        if update['atomic_aggregate']:
            print 'ATOMIC_AGGREGATE: %s' % update['atomic_aggregate']
        if update['aggregator_as']:
            print 'AGGREGATOR: AS%s %s' % (update['aggregator_as'], update['aggregator_ip'])
        if update['originator_id']:
            print 'ORIGINATOR_ID: %s' % update['originator_id']
        if update['cluster_list']:
            print 'CLUSTER_LIST: %s' % ' '.join(update['cluster_list'])
        if update['communities']:
            print 'COMMUNITIES: %s' % ' '.join(update['communities'])
        if update['announced']:
            print 'ANNOUNCED: \n   %s' % '\n   '.join(update['announced'])
        if update['withdrawn']:
            print 'WITHDRAWN: \n   %s' % '\n   '.join(update['withdrawn'])
        print ''
    elif FLAGS.print_updates == 2:
        print 'DATE / FROM: %s / %s AS%d' % (update['date'], update['from_ip'], update['from_as'])

def filter_announced_or_withdrawn(filter, prefixes):
    for i, attr in enumerate(filter, start=0):
        attr_split = attr.split('/')
        if len(attr_split) == 2:
            if attr not in prefixes:
                if FLAGS.filter_type == "or" and i != len(filter)-1:
                    continue
                else:
                    return False
            else:
                if FLAGS.filter_type == "or":
                        break
        else:
            ip_attr = IPAddress(attr)
            found = False
            for prefix in prefixes:
                if ip_attr in IPNetwork(prefix):
                    found = True
            if not found:
                if FLAGS.filter_type == "or" and i != len(filter)-1:
                    continue
                else:
                    return False
            else:
                if FLAGS.filter_type == "or":
                        break

    return True

# for communities, we might want to do some more specific parsing
def filter_communities(filter, communities):
    comm_split = []
    for community in communities:
        for _as in community.split(':'):
            comm_split.append(_as)
    for i, attr in enumerate(filter, start=0):
        if attr not in communities and attr not in comm_split:
            if FLAGS.filter_type == "or" and i != len(filter)-1:
                continue
            else:
                return False
        else:
            if FLAGS.filter_type == "or":
                    break

    return True

# run the specified filters on the BGP update
def filter_update(update):
    for filter in filters:
        if filter[0] == "route":
            if update['announced']:
                if filter_announced_or_withdrawn(filter[1], update['announced']):
                    continue
            if update['withdrawn']:
                if filter_announced_or_withdrawn(filter[1], update['withdrawn']):
                    continue
            return False

        elif update[filter[0]]:
            if filter[0] == "communities":
                if not filter_communities(filter[1], update['communities']):
                    return False
            elif filter[0] == "withdrawn" or filter[0] == "announced":
                if not filter_announced_or_withdrawn(filter[1], update[filter[0]]):
                    return False
            else:
                for i, attr in enumerate(filter[1], start=0):
                    if attr != update[filter[0]] and attr not in update[filter[0]]:
                        if FLAGS.filter_type == "or" and i != len(filter[1])-1:
                            continue
                        else:
                            return False
                    else:
                        if FLAGS.filter_type == "or":
                            break

        else:
            return False

    return True

# loops through all BGP updates in the file, and:
# i) parses the data, ii) puts it into a list of dictionaries, and iii) puts the timestamps of the updates in a file
def parse_updates(dump):
    try:
        for (mrt_h, bgp_h, bgp_m) in dump:
            # initialize dictionary of this update message
            update = empty_update()

            # parse date
            update['date'] = time.strftime('%D %T', time.gmtime(mrt_h.ts))
            update_date_unix = update_date_to_unix_timestamp(update['date'])

            # filter on date
            if FLAGS.date != "any":
                if update_date_unix not in dates_unix:
                    continue
            if start_date_unix != 0:
                if start_date_unix > update_date_unix:
                    continue
            if end_date_unix != 0:
                if end_date_unix < update_date_unix:
                    continue

            # parse from and to
            update['from_ip'] = dnet.ip_ntoa(bgp_h.src_ip)
            update['from_as'] = bgp_h.src_as 
            update['to_ip'] = dnet.ip_ntoa(bgp_h.dst_ip)
            update['to_as'] = bgp_h.dst_as

            # parse attributes
            for attr in bgp_m.update.attributes:
                if attr.type == bgp.ORIGIN:
                    update['origin'] = origin_to_str(attr.origin)
                elif attr.type == bgp.AS_PATH:
                    update['as_path'] = aspath_to_array(attr.as_path)
                elif attr.type == bgp.NEXT_HOP:
                    update['next_hop'] = dnet.ip_ntoa(attr.next_hop.ip)
                elif attr.type == bgp.MULTI_EXIT_DISC:
                    update['multi_exit_disc'] = attr.multi_exit_disc.value
                elif attr.type == bgp.LOCAL_PREF:
                    update['local_pref'] = attr.local_pref.value
                elif attr.type == bgp.ATOMIC_AGGREGATE:
                    update['atomic_aggregate'] = 'AG'
                elif attr.type == bgp.AGGREGATOR:
                    try:
                        update['aggregator_as'] = attr.as4_aggregator.asn
                        update['aggregator_ip'] = dnet.ip_ntoa(attr.as4_aggregator.ip)
                    except AttributeError:
                        update['aggregator_as'] = attr.aggregator.asn
                        update['aggregator_ip'] = dnet.ip_ntoa(attr.aggregator.ip)
                elif attr.type == bgp.ORIGINATOR_ID:
                    update['originator_id'] = dnet.ip_ntoa(attr.originator_id.value)
                elif attr.type == bgp.CLUSTER_LIST:
                    update['cluster_list'] = clusterlist_to_array(attr.cluster_list)
                elif attr.type == bgp.COMMUNITIES:
                    update['communities'] = communities_to_array(attr.communities)

            # parse announced
            if len(bgp_m.update.announced) > 0:
                update['announced'] = announced_or_withdrawn_to_array(bgp_m.update.announced)
                if FLAGS.find_origin != "no":
                    ip_attr = IPAddress(FLAGS.find_origin)
                    for prefix in update['announced']:
                        if ip_attr in IPNetwork(prefix):
                            prefix_cidr = prefix.split('/')[1]
                            print origin
                            if prefix_cidr > origin[0][0].split('/')[1]:
                                origin[0] = [prefix, update['as_path'][-1]]

            # parse withdrawn
            if len(bgp_m.update.withdrawn) > 0:
                update['withdrawn'] = announced_or_withdrawn_to_array(bgp_m.update.withdrawn)

            # filter on bgp fields and values
            if not filter_update(update):
                continue

            # print the update
            if FLAGS.print_updates > 0:
                print_update(update)
                
            #from_full = update['from_ip'] + "-AS" + str(update['from_as'])
            from_full = "AS" + str(update['from_as'])
            if from_full not in ip_freq:
                ip_freq[from_full] = 0
            ip_freq[from_full] += 1
            
            if from_full not in ip_long:
                ip_long[from_full] = {"value": 0, "last": update_date_unix}
            else:
                long = update_date_unix - ip_long[from_full]["last"]
                if long > ip_long[from_full]["value"]:
                    ip_long[from_full]["value"] = long
                ip_long[from_full]["last"] = update_date_unix
                
            if from_full not in ip_short:
                ip_short[from_full] = {"value": 100000, "last": update_date_unix}
            else:
                short = update_date_unix - ip_short[from_full]["last"]
                if short < ip_short[from_full]["value"]:
                    ip_short[from_full]["value"] = short
                ip_short[from_full]["last"] = update_date_unix
                
            if from_full not in intervals:
                intervals[from_full] = {"list": [], "last": update_date_unix, "saved": 0}
            else:
                #if len(intervals[from_full]["list"]) >= 5000:
                    #continue
                
                entry = float(update_date_unix - intervals[from_full]["last"])
                
                if entry >= FLAGS.at:
                    intervals[from_full]["list"].append(intervals[from_full]["saved"])
                    intervals[from_full]["saved"] = 0
                    intervals[from_full]["last"] = update_date_unix
                    new_entry = entry
                    
                    while True:
                        new_entry = new_entry - FLAGS.at
                        
                        if FLAGS.at >= new_entry:#or len(intervals[from_full]["list"]) >= 5000:
                            break
                        
                        intervals[from_full]["list"].append(0)
                    
                else:
                    intervals[from_full]["saved"] += 1

            # add and save the update
            #updates.append(update)
            #plots.append(update_date_unix)
    except:
        pass
            
# if we are dealing with ripe BGP files (which we pretty much always do in this case), we can actually infer
# if it is even worth parsing the file at all, based on the naming convention of the files
def ripe_date_check(file):
    check_file = True
    file_arr = file.split('.')
    file_date = '%s%s' % (file_arr[1], file_arr[2])
    file_date_arr = [file_date[0:4], file_date[4:6], file_date[6:8], file_date[8:10], file_date[10:12]]
    file_date_unix = array_to_unix_timestamp(file_date_arr)

    if start_date_unix != 0:
        if start_date_unix > file_date_unix:
            check_file = False
    if end_date_unix != 0:
        if end_date_unix < file_date_unix:
            check_file = False

    return check_file

# for converting input dates to unix-time
def input_date_to_unix_timestamp(date):
    date_arr = date.split('.')
    date_arr[0] = format_year(date_arr[0])
    date_unix = array_to_unix_timestamp(date_arr)
    return date_unix

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parses BGP update messages from files in MTR format. Files are either uncompressed or compressed in GZ files.")
    parser.add_argument("--input", default="dumps/sample.dump.gz", nargs='*')
    parser.add_argument("--print_updates", type=int, default=0)
    parser.add_argument("--save_timestamps", default="saved_ts/dump.bgp")
    parser.add_argument("--save_from", default="saved_lists/00/")
    parser.add_argument("--ripe", type=int, default=1)
    parser.add_argument("--find_origin", default="no")
    parser.add_argument("--filter_type", default="and")
    parser.add_argument("--at", type=int, default=1)

    # filters that can be used
    parser.add_argument("--start_date", default="any")
    parser.add_argument("--end_date", default="any")
    parser.add_argument("--date", default="any", nargs='*')
    parser.add_argument("--from_ip", default="any", nargs='*')
    parser.add_argument("--from_as", default="any", nargs='*')
    parser.add_argument("--to_ip", default="any", nargs='*')
    parser.add_argument("--to_as", default="any", nargs='*')
    parser.add_argument("--origin", default="any", nargs='*')
    parser.add_argument("--as_path", default="any", nargs='*')
    parser.add_argument("--next_hop", default="any", nargs='*')
    parser.add_argument("--multi_exit_disc", default="any", nargs='*')
    parser.add_argument("--local_pref", default="any", nargs='*')
    parser.add_argument("--atomic_aggregate", default="any", nargs='*')
    parser.add_argument("--aggregator_as", default="any", nargs='*')
    parser.add_argument("--aggregator_ip", default="any", nargs='*')
    parser.add_argument("--originator_id", default="any", nargs='*')
    parser.add_argument("--cluster_list", default="any", nargs='*')
    parser.add_argument("--communities", default="any", nargs='*')
    parser.add_argument("--announced", default="any", nargs='*')
    parser.add_argument("--withdrawn", default="any", nargs='*')
    parser.add_argument("--route", default="any", nargs='*')

    # perform no filtering on these args. dates are a special case, and are handled seperately
    no_filtering = ['input', 'print_updates', 'at', 'save_timestamps', 'save_from', 'ripe', 'start_date', 'end_date', 'date', 'find_origin', 'filter_type']
    FLAGS = parser.parse_args()

    if FLAGS.find_origin != "no":
        origin.append(['0/0', '0'])

    # add any specified filters to the filter-array
    for arg in vars(FLAGS):
        attr = getattr(FLAGS, arg)
        if attr != "any" and arg not in no_filtering:
            print arg
            if not isinstance(attr, list):
                attr = [attr]
            filters.append([arg, attr])

    # time/date is converted from yy.mm.dd.hh.mm.ss format to unix-time format, to be used in comparisons
    if FLAGS.start_date != "any":
        start_date_unix = input_date_to_unix_timestamp(FLAGS.start_date)
    if FLAGS.end_date != "any":
        end_date_unix = input_date_to_unix_timestamp(FLAGS.end_date)
    if FLAGS.date != "any":
        if isinstance(FLAGS.date, list):
            for date in FLAGS.date:
                date_unix = input_date_to_unix_timestamp(date)
                dates_unix.append(date_unix)
        else:
            date_unix = input_date_to_unix_timestamp(FLAGS.date)
            dates_unix.append(date_unix)

    # process all the specified input files/folders containing BGP data
    if not isinstance(FLAGS.input, list):
        inputs = [FLAGS.input]
    else:
        inputs = FLAGS.input
    for input_arg in inputs:
        if os.path.isdir(input_arg):        # if folder is given as input
            files = os.listdir(input_arg)   # list all files
            if FLAGS.ripe == 1:             # because of the naming convention of the ripe update files, we can sort them by name
                files.sort()

            for file in files:              # for each file, get the full path for it, then process it
                if FLAGS.ripe == 1 and not ripe_date_check(file):
                    continue

                file = input_arg + file
                print file
                if os.path.isdir(file):     # if file is actually a folder, skip it (todo: add folder recursion)
                    continue
                dump = BGPDump(file)        # get the BGP data from the file
                parse_updates(dump)         # process the file

        else:                               # if file is given as input
            print input_arg
            file_arr = input_arg.split('/')
            file = file_arr[-1]
            if not FLAGS.ripe == 1 or ripe_date_check(file):
                dump = BGPDump(input_arg)   # get the BGP data from the file
                parse_updates(dump)         # process the file

    if FLAGS.find_origin != "no":
        print "IP: %s, AS:%s" % (FLAGS.find_origin, origin[0][1])
		
    #if not os.path.exists(FLAGS.save_timestamps):  # if specified output file does not exist, create it
    file_append = open(FLAGS.save_from + "info.data", "a")
    file_append.write(".")
    file_append.flush()
    file_append.close()
    
    file_append = open(FLAGS.save_from + "info.data", "w")
    file_append.write("PEER / TOT UPDATES / AVG. PER MIN / LONG / SHORT" + "\n")
    
    tot_updates = 0
    for key, val in ip_freq.iteritems():
        avg_min = float(val) / (24.0 * 60.0)
        file_append.write(str(key) + " / " + str(val) + " / " + str(avg_min) + " / " + str(ip_long[key]["value"]) + " / " + str(ip_short[key]["value"]) + "\n")
        tot_updates += val
        
    file_append.write("Total number of updates: " + str(tot_updates) + "\n")
    file_append.flush()
    file_append.close()
        
    for key in intervals.iterkeys():
        file_append_peer = open(FLAGS.save_from + key, "a")
        file_append_peer.write(".")
        file_append_peer.flush()
        file_append_peer.close()            
        file_append_peer = open(FLAGS.save_from + key, "w")
        
        for entry in intervals[key]["list"]:
            file_append_peer.write(str(entry) + "\n")
        
        file_append_peer.flush()
        file_append_peer.close()           
