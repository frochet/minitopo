from core.experiment import RandomFileExperiment, RandomFileParameter, ExperimentParameter
from topos.multi_interface_multi_client import MultiInterfaceMultiClientConfig
import os
import time

class TCPLSParameter(ExperimentParameter):
    #can be on or off
    FAILOVER = "failover"
    # one of the client/server interface name
    CLIENT_BACKUP_IF = "clientBackupIF"
    SERVER_BACKUP_IF = "serverBackupIF"
    # Can be none, drop, rst or ifupdown
    PERTURBATION = "perturbationType"
    GOODPUT_FILE = "goodputFile"
    INTERVAL = "interval"

    def __init__(self, experiment_parameter_filename):
        super(TCPLSParameter, self).__init__(experiment_parameter_filename)
        self.default_parameters.update({
            TCPLSParameter.FAILOVER : "on",
            TCPLSParameter.CLIENT_BACKUP_IF: "none",
            TCPLSParameter.SERVER_BACKUP_IF: "none",
            TCPLSParameter.GOODPUT_FILE: "none",
            TCPLSParameter.PERTURBATION: "drop",
            TCPLSParameter.INTERVAL: 5,
        })

class TCPLS(RandomFileExperiment):
    NAME = "tcpls"
    PARAMETER_CLASS = TCPLSParameter
    CLI = "~/picotcpls/cli"
    SERVER_LOG = "tcpls_server.log"
    CLIENT_LOG = "tcpls_client.log"
    CERT = "~/picotcpls/t/assets/server.crt"
    KEY = "~/picotcpls/t/assets/server.key"
    DROP_SCRIPT = "~/picotcpls/t/ipmininet/tcp_drop.sh"
    RST_SCRIPT = "~/picotcpls/t/ipmininet/tcp_reset_mininet.sh"
    IFUPDOWN_SCRIPT = "/tutorial/08_tcpls/ifupdown_client.sh"

    def __init__(self, experiment_parameter_filename, topo, topo_config):
        super(TCPLS, self).__init__(experiment_parameter_filename, topo, topo_config)
        self.load_parameters()

    def load_parameters(self):
        super(TCPLS, self).load_parameters()
        self.failover = self.experiment_parameter.get(TCPLSParameter.FAILOVER)
        self.goodputFile = self.experiment_parameter.get(TCPLSParameter.GOODPUT_FILE)
        self.perturbationType = self.experiment_parameter.get(TCPLSParameter.PERTURBATION)
        if self.failover == "on":
            self.failover_flag = "-f"
        else:
            self.failover_flag = ""
        if self.goodputFile != "none":
            self.goodput_flag = "-g "+self.goodputFile
        else:
            self.goodput_flag = ""
        self.interval = int(self.experiment_parameter.get(TCPLSParameter.INTERVAL))
    
    def ping(self):
        pass

    def prepare(self):
        super(TCPLS, self).prepare()
        self.topo.command_to(self.topo_config.client, "rm " + \
                             TCPLS.CLIENT_LOG )
        self.topo.command_to(self.topo_config.server, "rm " + \
                             TCPLS.SERVER_LOG )

    def getServerCmd(self):
        IP_PRIMARY = self.topo_config.get_server_ip(0)
        IP_SECONDARY = self.topo_config.get_server_ip(1)
        s =  ""+TCPLS.CLI+" -t "+self.failover_flag+" -T simple_transfer -k "+TCPLS.KEY+" -c "+TCPLS.CERT+" -i "+self.file+" -z "+IP_SECONDARY+" "+IP_PRIMARY+" 4443 &"
        print(s)
        return s

    def getClientCmd(self):
        IP_PRIMARY = self.topo_config.get_server_ip(0)
        IP_SECONDARY = self.topo_config.get_server_ip(1)
        
        CLIENT_PRIMARY = self.topo_config.get_client_ip(0)
        CLIENT_SECONDARY = self.topo_config.get_client_ip(1)

        s= ""+TCPLS.CLI+" -t "+self.failover_flag+" "+self.goodput_flag+" -T simple_transfer -z "+CLIENT_PRIMARY+" -z "+CLIENT_SECONDARY+" -p "+IP_SECONDARY+" "+IP_PRIMARY+" 4443 &"
        print(s)
        return s


    def run(self):
        self.topo.command_to(self.topo_config.client, "ip link set dev Client_0-eth1 multipath backup")
        self.topo.command_to(self.topo_config.server, "ip link set dev Server_0-eth1 multipath backup")
        #self.topo.command_to(self.topo_config.client, "ip route add 10.1.1.0/24 via 10.0.1.2 dev Client_0-eth1")
        self.topo.command_to(self.topo_config.server, self.getServerCmd())
        # ensure the server has started -- 1 sec should be enough
        self.topo.command_to(self.topo_config.client, " tcpdump -i any -n -v host 10.1.0.1 or 10.1.1.1 &> client_tcpdump.log&")

        self.topo.command_to(self.topo_config.client, "sleep 1")
        self.topo.command_to(self.topo_config.client, self.getClientCmd())
        if self.perturbationType == "drop":
            bin = TCPLS.DROP_SCRIPT
        elif self.perturbationType == "rst":
            bin = TCPLS.RST_SCRIPT
            self.topo.command_to(self.topo_config.router, ""+bin+" "+str(self.interval)+" &")
        elif self.perturbationType == "ifupdown":
            bin = TCPLS.IFUPDOWN_SCRIPT
            self.topo.command_to(self.topo_config.client, ""+bin+" "+str(self.interval)+" &> ifupdown.log")
        else:
            print("does not know what to do with {}".format(self.perturbationType))
        time.sleep(80)

    def clean(self):
        super(TCPLS, self).clean()
        self.topo.command_to(self.topo_config.router, "iptables -F")

