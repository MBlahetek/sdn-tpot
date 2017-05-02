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
container_ip_list = []

#Connect all docker0 containers to the ovs bridge
"""
for i in bridge_docker_container:
    attributes = i.attrs
    name = str(attributes["Name"])
    name = name[1:]
    ip_bridge_docker = str(attributes["NetworkSettings"]["Networks"]["bridge"]["IPAddress"])
    bridge_ovs.connect(name)
    container_ip_list.append([name, ip_bridge_docker])
    
for i in container_ip_list:
    name = i[0]
    container = client.containers.get(name)
    ip_bridge_ovs = str(container.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"])
    i = i.append(ip_bridge_ovs)
"""        
ovs_bridge_name = rf.get_ovs_bridge_name()
if ovs_bridge_name is None:
    raise NameError("no ovs bridge found")
print ovs_bridge_name

table_filter = iptc.Table(iptc.Table.FILTER)
#table_nat = iptc.Table(iptc.Table.NAT)

chain_filter_forward = iptc.Chain(table_filter, "FORWARD")
chain_filter_docker = iptc.Chain(table_filter, "DOCKER")
#chains_nat = table_nat.chains

rules_filter_forward = chain_filter_forward.rules

for r in rules_filter_forward:
    new_rule = r
    """    
    new_rule.dst = r.dst
    new_rule.fragment = r.fragment
    #new_rule.mask = r.mask
    #new_rule.matches = r.matches
    new_rule.protocol = r.protocol
    if r.in_interface is not None:
        new_rule.in_interface = r.in_interface
    if r.out_interface is not None:
        new_rule.out_interface = r.out_interface
    #new_rule.rule = r.rule
    new_rule.src = r.src
    #new_rule.tables = r.tables
    new_rule.target = r.target
    chain_filter_forward.append_rule(new_rule)
    """
    if r.in_interface is not None:
        if r.in_interface == "docker0":
            new_rule.in_interface = ovs_bridge_name
        elif r.in_interface == "!docker0":
            new_rule.in_interface = "!" + ovs_bridge_name
    if r.out_interface is not None:
        if r.out_interface == "docker0":
            new_rule.out_interface = ovs_bridge_name
        elif r.out_interface == "!docker0":
            new_rule.out_interface = "!" + ovs_bridge_name
    chain_filter_forward.append_rule(new_rule)

#print chains_filter
#print chains_nat