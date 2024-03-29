# shared "database" of ip, prefix, and bgp mappings

ip_to_prefix_dict = {"10.0.1.0": "10.0.1.0/24", "10.0.2.0": "10.0.2.0/24", "10.0.3.0": "10.0.3.0/24",
                     "10.0.4.0": "10.0.4.0/24", "10.0.5.0": "10.0.5.0/24", "10.0.6.0": "10.0.6.0/24",
                     "10.0.7.0": "10.0.7.0/24", "10.0.8.0": "10.0.8.0/24", "10.0.9.0": "10.0.9.0/24",
                     "10.0.10.0": "10.0.10.0/24", "10.0.11.0": "10.0.11.0/24", "10.0.12.0": "10.0.12.0/24", 
                     "10.0.13.0": "10.0.13.0/24", "10.0.14.0": "10.0.14.0/24", "10.0.15.0": "10.0.15.0/24", 
                     "10.0.16.0": "10.0.16.0/24", "10.0.17.0": "10.0.17.0/24", "10.0.18.0": "10.0.18.0/24", 
                     "10.0.19.0": "10.0.19.0/24", "10.0.20.0": "10.0.20.0/24", "10.0.21.0": "10.0.21.0/24", 
                     "10.0.22.0": "10.0.22.0/24", "10.0.23.0": "10.0.23.0/24", "10.0.24.0": "10.0.24.0/24", 
                     "10.0.25.0": "10.0.25.0/24", "10.0.26.0": "10.0.26.0/24"}

ip_to_asn_dict = {"10.0.1.0": "100", "20.0.1.1": "100", "20.0.2.1": "100", "20.1.0.1": "100", "20.1.0.2": "100", "20.0.51.1": "100", 
                 "10.0.2.0": "200", "20.0.1.2": "200", "20.0.3.1": "200", "20.2.0.1": "200", "20.2.0.2": "200", "20.0.52.1": "200", 
                 "10.0.3.0": "300", "20.0.3.2": "300", "20.0.4.1": "300", "20.3.0.1": "300", "20.3.0.2": "300", "20.0.53.1": "300", 
                 "10.0.4.0": "400", "20.0.4.2": "400", "20.0.5.1": "400", "20.4.0.1": "400", "20.4.0.2": "400", "20.0.54.1": "400", 
                 "10.0.5.0": "500", "20.0.5.2": "500", "20.0.6.1": "500", "20.5.0.1": "500", "20.5.0.2": "500", "20.0.55.1": "500", 
                 "10.0.6.0": "600", "20.0.6.2": "600", "20.0.7.1": "600", "20.6.0.1": "600", "20.6.0.2": "600", "20.0.56.1": "600", 
                 "10.0.7.0": "700", "20.0.2.2": "700", "20.0.8.1": "700", "20.7.0.1": "700", "20.7.0.2": "700", 
                 "10.0.8.0": "800", "20.0.8.2": "800", "20.0.9.1": "800", "20.8.0.1": "800", "20.8.0.2": "800", 
                 "10.0.9.0": "900", "20.0.9.2": "900", "20.0.10.1": "900", "20.9.0.1": "900", "20.9.0.2": "900", 
                 "10.0.10.0": "1000", "20.0.10.2": "1000", "20.0.11.1": "1000", "20.10.0.1": "1000", "20.10.0.2": "1000", 
                 "10.0.11.0": "1100", "20.0.11.2": "1100", "20.0.12.1": "1100", "20.11.0.1": "1100", "20.11.0.2": "1100", 
                 "10.0.12.0": "1200", "20.0.12.2": "1200", "20.0.13.1": "1200", "20.12.0.1": "1200", "20.12.0.2": "1200", 
                 "10.0.13.0": "1300", "20.0.7.2": "1300", "20.0.13.2": "1300", "20.13.0.1": "1300", "20.13.0.2": "1300"}                
                 
local_ip = ""
local_asn = ""

def set_local_ip_asn(ip):
    global local_ip
    local_ip = ip
    global local_asn
    local_asn = ip_to_asn(ip)

def ip_truncated(ip):
    ip_list = ip.split(".")
    ip_list[3] = "0"
    return ".".join(ip_list)

def ip_to_prefix(ip):
    if ip.startswith("10"):
        ip = ip_truncated(ip)

    if ip in ip_to_prefix_dict:
        return ip_to_prefix_dict[ip]
    else:
        return "*"

def ip_to_asn(ip):
    if ip.startswith("10"):
        ip = ip_truncated(ip)

    if ip in ip_to_asn_dict:
        return ip_to_asn_dict[ip]
    else:
        return "*"
