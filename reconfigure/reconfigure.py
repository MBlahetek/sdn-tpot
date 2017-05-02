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
        
ovs_bridge_name = rf.get_ovs_bridge_name()
if ovs_bridge_name is None:
    raise NameError("no ovs bridge found")

table_filter = iptc.Table(iptc.Table.FILTER)
table_nat = iptc.Table(iptc.Table.NAT)
chain_filter_forward = iptc.Chain(table_filter, "FORWARD")
chain_filter_docker = iptc.Chain(table_filter, "DOCKER")
chain_nat_postrouting = iptc.Chain(table_nat, "POSTROUTING")
chain_nat_docker = iptc.Chain(table_nat, "DOCKER")

rf.update_iptables_chain(chain_filter_forward, container_ip_list)
rf.update_iptables_chain(chain_filter_docker, container_ip_list)
rf.update_iptables_chain(chain_nat_postrouting, container_ip_list)
rf.update_iptables_chain(chain_nat_docker, container_ip_list)

for i in container_ip_list:
    name = i[0]
    bridge_docker.disconnect(name)