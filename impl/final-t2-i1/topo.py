#!/usr/bin/python

import inspect
import os
from mininext.topo import Topo
from mininext.services.quagga import QuaggaService
from collections import namedtuple

QuaggaHost = namedtuple("QuaggaHost", "name ip mac")
net = None
# Directory where this file / script is located
selfPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
# Initialize a service helper for Quagga with default options
quaggaSvc = QuaggaService(autoStop=False)
# Path configurations for mounts
quaggaBaseConfigPath = selfPath + "/configs/"

class QuaggaTopo(Topo):
    def addQuaggaLinks(self, quaggas):
        self.addLink(quaggas["100_r1"], quaggas["5100_rt"], delay="10ms")
        self.addLink(quaggas["200_r1"], quaggas["5200_rt"], delay="10ms")
        self.addLink(quaggas["300_r1"], quaggas["5300_rt"], delay="10ms")
        self.addLink(quaggas["400_r1"], quaggas["5400_rt"], delay="10ms")
        self.addLink(quaggas["600_r1"], quaggas["5600_rt"], delay="10ms")
        
        self.addLink(quaggas["100_r1"], quaggas["200_r1"], delay="10ms")
        self.addLink(quaggas["200_r1"], quaggas["300_r1"], delay="10ms")
        self.addLink(quaggas["200_r1"], quaggas["600_r1"], delay="10ms")
        self.addLink(quaggas["300_r1"], quaggas["900_r1"], delay="10ms")
        self.addLink(quaggas["300_r1"], quaggas["400_r1"], delay="10ms")
        self.addLink(quaggas["400_r1"], quaggas["900_r1"], delay="10ms")
        self.addLink(quaggas["400_r1"], quaggas["500_r1"], delay="10ms")
        self.addLink(quaggas["500_r1"], quaggas["800_r1"], delay="10ms")
        self.addLink(quaggas["500_r1"], quaggas["1100_r1"], delay="10ms")
        self.addLink(quaggas["600_r1"], quaggas["700_r1"], delay="10ms")
        self.addLink(quaggas["700_r1"], quaggas["1000_r1"], delay="10ms")
        self.addLink(quaggas["700_r1"], quaggas["800_r1"], delay="10ms")

    def addHostToQuagga(self, quaggas, quagga):
        quagga_split = quagga.split("_")
        host_name = quagga_split[0] + "_h1"
        network = quagga.split("00_")[0]
        host_ip = "10.0." + network + ".20/24"
    
        host = self.addHost(name=host_name, ip=host_ip, hostname=host_name, 
        privateLogDir=True, privateRunDir=True, inMountNamespace=True, inPIDNamespace=True, inUTSNamespace=True)
        self.addLink(host, quaggas[quagga])
    
    def addHosts(self, quaggas):
        self.addHostToQuagga(quaggas, "100_r1")
        self.addHostToQuagga(quaggas, "200_r1")
        self.addHostToQuagga(quaggas, "300_r1")
        self.addHostToQuagga(quaggas, "400_r1")
        self.addHostToQuagga(quaggas, "500_r1")
        self.addHostToQuagga(quaggas, "600_r1")
        self.addHostToQuagga(quaggas, "700_r1")
        self.addHostToQuagga(quaggas, "800_r1")
        self.addHostToQuagga(quaggas, "900_r1")
        self.addHostToQuagga(quaggas, "1000_r1")
        self.addHostToQuagga(quaggas, "1100_r1")

    def addQuaggas(self):
        quaggaHosts = []
        quaggaHosts.append(QuaggaHost(name="100_r1", ip="10.0.1.10/24", mac="00:00:00:01:00:10"))
        quaggaHosts.append(QuaggaHost(name="200_r1", ip="10.0.2.10/24", mac="00:00:00:02:00:10"))
        quaggaHosts.append(QuaggaHost(name="300_r1", ip="10.0.3.10/24", mac="00:00:00:03:00:10"))
        quaggaHosts.append(QuaggaHost(name="400_r1", ip="10.0.4.10/24", mac="00:00:00:04:00:10"))
        quaggaHosts.append(QuaggaHost(name="500_r1", ip="10.0.5.10/24", mac="00:00:00:05:00:10"))
        quaggaHosts.append(QuaggaHost(name="600_r1", ip="10.0.6.10/24", mac="00:00:00:06:00:10"))
        quaggaHosts.append(QuaggaHost(name="700_r1", ip="10.0.7.10/24", mac="00:00:00:07:00:10"))
        quaggaHosts.append(QuaggaHost(name="800_r1", ip="10.0.8.10/24", mac="00:00:00:08:00:10"))
        quaggaHosts.append(QuaggaHost(name="900_r1", ip="10.0.9.10/24", mac="00:00:00:09:00:10"))
        quaggaHosts.append(QuaggaHost(name="1000_r1", ip="10.0.10.10/24", mac="00:00:00:10:00:10"))
        quaggaHosts.append(QuaggaHost(name="1100_r1", ip="10.0.11.10/24", mac="00:00:00:11:00:10"))
        
        quaggaHosts.append(QuaggaHost(name="5100_rt", ip="20.0.51.2/30", mac="00:00:00:51:00:10"))
        quaggaHosts.append(QuaggaHost(name="5200_rt", ip="20.0.52.2/30", mac="00:00:00:52:00:10"))
        quaggaHosts.append(QuaggaHost(name="5300_rt", ip="20.0.53.2/30", mac="00:00:00:53:00:10"))
        quaggaHosts.append(QuaggaHost(name="5400_rt", ip="20.0.54.2/30", mac="00:00:00:54:00:10"))
        quaggaHosts.append(QuaggaHost(name="5600_rt", ip="20.0.56.2/30", mac="00:00:00:56:00:10"))
        return quaggaHosts

    def __init__(self):
        Topo.__init__(self)
        # List of Quagga host configs
        quaggaHosts = self.addQuaggas()

        quaggas = {}
        # Setup each Quagga router
        for host in quaggaHosts:
            # Create an instance of a host, called a quaggaContainer
            quaggaContainer = self.addHost(name=host.name, ip=host.ip, hostname=host.name, mac=host.mac,
                                           privateLogDir=True, privateRunDir=True, inMountNamespace=True,
                                           inPIDNamespace=True, inUTSNamespace=True)
            # Configure and setup the Quagga service for this node
            quaggaSvcConfig = {"quaggaConfigPath": quaggaBaseConfigPath + host.name}
            self.addNodeService(node=host.name, service=quaggaSvc, nodeConfig=quaggaSvcConfig)
            # Save it
            quaggas[host.name] = quaggaContainer

        # Add one host to each router
        self.addHosts(quaggas)        
        # Links between routers
        self.addQuaggaLinks(quaggas)
