#!/usr/bin/python

import sys
import atexit
import mininet.util
import mininext.util
from mininet.util import dumpNodeConnections
from mininet.node import OVSSwitch
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininext.cli import CLI
from mininext.net import MiniNExT
from topo import QuaggaTopo
import ip_bgp_data

mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules["mininet.util"] = mininet.util
net = None

def config_network(quagga_name, quagga_ips):
    # Enable IP forwarding
    net.get(quagga_name).cmd("sudo echo '1' > /proc/sys/net/ipv4/ip_forward")
    
    # Disable rp-filtering
    net.get(quagga_name).cmd("sudo sysctl -w net.ipv4.conf.lo.rp_filter=0")
    net.get(quagga_name).cmd("sudo sysctl -w net.ipv4.conf.all.rp_filter=0")
    net.get(quagga_name).cmd("sudo sysctl -w net.ipv4.conf.default.rp_filter=0")
    net.get(quagga_name).cmd("sudo sysctl -w net.ipv4.conf." + str(quagga_name) + "-eth0.rp_filter=0")

    for i in range(0, len(quagga_ips)):
        net.get(quagga_name).cmd("sudo ifconfig " + quagga_name + "-eth" + str(i + 1) + " " + quagga_ips[i] + " netmask 255.255.255.252")
        net.get(quagga_name).cmd("sudo sysctl -w net.ipv4.conf." + str(quagga_name) + "-eth" + str(i + 1) + ".rp_filter=0") 
        
    quagga_split = quagga_name.split("_")
    asn = quagga_split[0]
    router = quagga_split[1]
    network = quagga_name.split("00_")[0]
    ip = "10.0." + network + ".10"
    
    if router == "r1":
        host_name = asn + "_h1"
        net.get(host_name).cmd("sudo route add default gw " + ip + " " + host_name + "-eth0")
        
    net.get(quagga_name).cmd("sudo sysctl -p")

def config_components():
    config_network("100_r1", ["20.0.51.1", "20.0.1.1", "20.0.2.1"])
    config_network("200_r1", ["20.0.52.1", "20.0.1.2", "20.0.3.1"])
    config_network("300_r1", ["20.0.53.1", "20.0.3.2", "20.0.4.1"])
    config_network("400_r1", ["20.0.54.1", "20.0.4.2", "20.0.5.1"])
    config_network("500_r1", ["20.0.55.1", "20.0.5.2", "20.0.6.1"])
    config_network("600_r1", ["20.0.56.1", "20.0.6.2", "20.0.7.1"])
    config_network("700_r1", ["20.0.2.2", "20.0.8.1"])
    config_network("800_r1", ["20.0.8.2", "20.0.9.1"])
    config_network("900_r1", ["20.0.9.2", "20.0.10.1"])
    config_network("1000_r1", ["20.0.10.2", "20.0.11.1"])
    config_network("1100_r1", ["20.0.11.2", "20.0.12.1"])
    config_network("1200_r1", ["20.0.12.2", "20.0.13.1"])
    config_network("1300_r1", ["20.0.7.2", "20.0.13.2"])
    
    config_network("5100_rt", [])
    config_network("5200_rt", [])
    config_network("5300_rt", [])
    config_network("5400_rt", [])
    config_network("5500_rt", [])
    config_network("5600_rt", [])

def setup_forwarder(node):
    dst = "10.0.1.10"
    src = net.get(node).IP(node + "-eth0")
    
    net.get(node).cmd("sudo python get_paths.py --src_ip " + src + " --dst_ip " + dst + " &")
    net.get(node).cmd("sudo python forwarder_zebra.py --src_ip " + src + " &")   
    net.get(node).cmd("sudo python forwarder_rcvd.py --src_ip " + src + " --dst_ip " + dst + " &")
    
def setup_services():
    setup_forwarder("100_r1")
    setup_forwarder("200_r1")
    setup_forwarder("300_r1")
    setup_forwarder("400_r1")
    setup_forwarder("500_r1")
    setup_forwarder("600_r1")
    setup_forwarder("700_r1")
    setup_forwarder("800_r1")
    setup_forwarder("900_r1")
    setup_forwarder("1000_r1")
    setup_forwarder("1100_r1")
    setup_forwarder("1200_r1")
    setup_forwarder("1300_r1")

def startNetwork():
    info("** Creating Quagga network topology\n")
    topo = QuaggaTopo()

    info("** Starting the network\n")
    global net
    net = MiniNExT(topo, controller=None, autoStaticArp=True, autoSetMacs=True, switch=OVSSwitch, link=TCLink)

    # Manual configuration and startup
    config_components()
    net.start()
    setup_services()
    
    #info('** Dumping host process(es)\n')
    #for host in net.hosts:
        #host.cmdPrint("ps aux")
    #net.get("100_r1").cmdPrint("ps aux")

    info("** Running CLI\n")
    CLI(net)

def stop_network():
    if net is not None:
        info("** Tearing down Quagga network\n")
        net.stop()

if __name__ == "__main__":
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stop_network)
    # Tell mininet to print useful information
    setLogLevel("info")
    # Start the simulation
    startNetwork()
