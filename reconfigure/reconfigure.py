'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
import iptc
import docker
import reconffunctions as rf

client = docker.from_env()

bridge_docker = client.networks.list('bridge')[0]
bridge_ovs = client.networks.list('sdnnet')[0]
bridge_docker_container = bridge_docker.containers

ovs_bridge_name = rf.get_ovs_bridge_name()
if ovs_bridge_name is None:
    raise NameError("no ovs bridge found")

container_ip_list = []

#Connect all docker0 containers to the ovs bridge
print "connecting docker container to ovs-bridge: " + ovs_bridge_name + "..."
for i in bridge_docker_container:
    attributes = i.attrs
    name = str(attributes["Name"])
    name = name[1:]
    ip_bridge_docker = str(attributes["NetworkSettings"]["Networks"]["bridge"]["IPAddress"])
    container_port_list = []
    for port in attributes["NetworkSettings"]["Ports"]:
        port_in = port.split("/", 1)[0] # port exposed by container, i.e. cowrie: 2222
        protocol = port.split("/", 1)[1] 
        port_ex = attributes["NetworkSettings"]["Ports"][port][0]["HostPort"] # original port, i.e. cowrie: 22
        container_port_list.append([port_ex, port_in, protocol])
    bridge_ovs.connect(name)
    container_ip_list.append([name, container_port_list, ip_bridge_docker])
    print "   container connected: " + name
print "##########"

print "generating ip mapping..."    
for i in container_ip_list:
    name = i[0]
    ip = i[2]
    container = client.containers.get(name)
    ip_bridge_ovs = str(container.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"])
    i = i.append(ip_bridge_ovs)
    print "   container: " + name + " | docker0 IP: " + ip + " | " + ovs_bridge_name + " IP: " + ip_bridge_ovs
print "##########"

table_filter = iptc.Table(iptc.Table.FILTER)
table_nat = iptc.Table(iptc.Table.NAT)
chain_filter_forward = iptc.Chain(table_filter, "FORWARD")
chain_filter_docker = iptc.Chain(table_filter, "DOCKER")
chain_nat_postrouting = iptc.Chain(table_nat, "POSTROUTING")
chain_nat_docker = iptc.Chain(table_nat, "DOCKER")

print "updating iptables..."
print "   updating table:FILTER chain:FORWARD..."
rf.update_iptables_chain(chain_filter_forward, container_ip_list, ovs_bridge_name)
print "   updating table:FILTER chain:DOCKER..."
rf.update_iptables_chain(chain_filter_docker, container_ip_list, ovs_bridge_name)
print "   updating table:FILTER chain:POSTROUTING..."
chain_nat_postrouting.delete_rule(chain_nat_postrouting.rules[0]) # delete the additional rule created by the docker ovs plugin
rf.update_iptables_chain(chain_nat_postrouting, container_ip_list, ovs_bridge_name)
print "   updating table:FILTER chain:DOCKER..."
rf.update_iptables_chain_dnat(chain_nat_docker, container_ip_list, ovs_bridge_name)
print "##########"

print "disconnecting docker container from docker0..."
for i in container_ip_list:
    name = i[0]
    bridge_docker.disconnect(name)
    print "   container disconnected: " + name
print "##########"
print ">>> reconfiguration complete! <<<"