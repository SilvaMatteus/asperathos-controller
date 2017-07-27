import ConfigParser
import paramiko

#from service.api.actuator.instance_locator import Instance_Locator
from service.api.actuator.plugins.instance_locator_tunnel import Instance_Locator_Tunnel
from service.api.actuator.plugins.remote_KVM_tunnel import Remote_KVM_Tunnel
#from service.api.actuator.remote_kvm import Remote_KVM
from utils.ssh_utils import SSH_Utils
from service.api.actuator.plugins.kvm_actuator import KVM_Actuator
from service.api.actuator.plugins.instance_locator import Instance_Locator
from service.api.actuator.plugins.remote_kvm import Remote_KVM
from service.api.actuator.plugins.nop_actuator import Nop_Actuator
from service.api.actuator.plugins.service_actuator import Service_Actuator
from service.api.actuator.plugins.service_instance_locator import Service_Instance_Locator
from service.api.actuator.plugins.kvm_up import KVM_Actuator_UPV


# TODO: documentation
class Actuator_Builder:

    def get_actuator(self, name):
        config = ConfigParser.RawConfigParser()
        config.read("scaler.cfg")
        
        if name == "kvm":
            compute_nodes_str = config.get("actuator", "compute_nodes")
            compute_nodes_keypair = config.get("actuator", "keypair_compute_nodes")
            compute_nodes = [x.strip() for x in compute_nodes_str.split(",")]
            
            instance_locator = Instance_Locator(SSH_Utils({}), compute_nodes, compute_nodes_keypair)
            remote_kvm = Remote_KVM(SSH_Utils({}), compute_nodes_keypair)
            return KVM_Actuator(instance_locator, remote_kvm)
        elif name == "kvm-tunnel":
            compute_nodes_str = config.get("actuator", "compute_nodes")
            compute_nodes_keypair = config.get("actuator", "keypair_compute_nodes")
            compute_nodes = [x.strip() for x in compute_nodes_str.split(",")]
            
            ports_str = config.get("actuator", "tunnel_ports")
            ports = [x.strip() for x in ports_str.split(",")]
            
            hosts_ports = {compute_nodes[i]:ports[i] for i in xrange(len(ports))}
            
            instance_locator = Instance_Locator_Tunnel(SSH_Utils(hosts_ports), compute_nodes, compute_nodes_keypair)
            remote_kvm = Remote_KVM_Tunnel(SSH_Utils(hosts_ports), compute_nodes_keypair)
            return KVM_Actuator(instance_locator, remote_kvm)
        elif name == "kvm-upv":
            conn = paramiko.SSHClient()
            conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            conn.connect(hostname=config.get("actuator", "access_ip"),
                         username=config.get("actuator", "access_username"),
                         password=config.get("actuator", "access_password"))

            conn.exec_command("ssh -i hostkey root@niebla.i3m.upv.edu")
            return KVM_Actuator_UPV(conn)
        elif name == "nop":
            return Nop_Actuator()
        elif name == "service":
            actuator_port = config.get("actuator", "actuator_port")
            
            compute_nodes_str = config.get("actuator", "compute_nodes")
            compute_nodes = [x.strip() for x in compute_nodes_str.split(",")]
            
            instance_locator = Service_Instance_Locator(compute_nodes, actuator_port)
            return Service_Actuator(actuator_port, instance_locator)
        else:
            # FIXME: review this exception type
            raise Exception("Unknown actuator type")
