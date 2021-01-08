from core.experiment import RandomFileExperiment, RandomFileParameter, ExperimentParameter
from topos.multi_interface_multi_client import MultiInterfaceMultiClientConfig
import os
import time

class TCPLSParameter(RandomFileExperiment):
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
            TCPLSParameter.FAILOVER : "off",
            TCPLSParameter.CLIENT_BACKUP_IF: "none",
            TCPLSParameter.SERVER_BACKUP_IF: "none",
            TCPLSParameter.GOODPUT_FILE: "none",
            TCPLSParameter.pperturbartionType: "drop",
            TCPLSParameter.INTERVAL: 5,
        })

class TCPLS(RandomFileExperiment):
    NAME = "tcpls"
    PARAMETER_CLASS = TCPLSParameter
    CLI = "~/picotcpls/cli
    SERVER_LOG = "tcpls_server.log"
    CLINET_LOG = "tcpls_client.log"
    CERT = "~/picotcpls/t/assets/server.crt"
    KEY = "~/picotcpls/t/assets/server.key"
    DROP_SCRIPT = "~/picotcpls/t/ipmininet/tcp_drop.sh"
    RST_SCRIPT = "~/picotcpls/t/ipmininet/tcp_reset_mininet.sh"

    def load_parameter(self):
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
                self.interval = self.experiment_parameter.get(TCPLSParameter.INTERVAL)
                self.drop_script = self.experiment_parameter.

    def prepare(self):
        super(TCPLS, self).prepare()
        self.topo.command_to(self.topo_config.client, "rm " + \
                             TCPLS.CLIENT_LOG )
        self.topo.command_to(self.topo_config.server, "rm " + \
                             TCPLS.SERVER_LOG )

    def getServerCmd(self):
        IP_PRIMARY = self.topo_config.get_server_ip(0)
        IP_SECONDARY = self.topo_config.get_server_ip(1)

        return ""+TCPLS.CLI+" -t "+self.failover_flag+" -T simple_transfert -k "+TCPLS.KEY+" -c "+TCPLS.CERT+" -i "+self.file+" -Z "+IP_SECONDARY+" "+IP_PRIMARY+" 4443 &"

    def getClientCmd(self):
        IP_PRIMARY = self.topo_config.get_server_ip(0)
        IP_SECONDARY = self.topo_config.get_server_ip(1)

        return ""+TCPLS.CLI+" -t "+self.failover_flag+" "+self.goodput_flag+" -T simple_transfert -P "+IP_SECONDARY+" "+IP_PRIMARY+" 4443 &"


    def run(self):
        self.top.command_to(self.topo_confif.server, self.getServerCmd)
        # ensure the server has started -- 1 sec should be enough
        self.topo.command_to(self.topo_config.client, "sleep 1")
        self.topo.command_to(self.topo_config.client, 
        self.topo.command_to(self.topo_config.client, self.getClientCmd)
        if self.perturbationType == "drop" or self.perturbationType == "rst":
            if self.perturbationType == "drop":
                bin = TCPLS.DROP_SCRIPT
            else:
                bin = TCPLS.RST_SCRIPT
            self.topo.command_to(self.top_config.router, ""+bin+" "+self.interval+" &")
            time.sleep(70)

        elif self.perturbationType == "ifupdown":
            ## ifupdown of the server link to the R
            nodelinks = [("bs_r2s_0_3", "Server_0"), ("bs_r2s_1_3","Server_0")]
            i = 0
            for _ in range(0, 70/self.interval):
                index = i%2
                index_next = (i+1)%2
                self.topo.net.configLinkStatus(nodelinks[index][0],
                                               nodelinks[index][1], "up")
                self.topo.net.configLinkStatus(nodelinks[index_next][0],
                                               nodelinks[index_next][1], "down")
                i+=1
                time.sleep(self.interval)



    def clean(self):
        super(TCPLS, self).clean()

