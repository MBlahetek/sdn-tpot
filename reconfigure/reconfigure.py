'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker
import reconffunctions as rf

client = docker.from_env()

bridge_docker = client.networks.list('bridge')[0]
bridge_ovs = client.networks.list('sdnnet')[0]
bridge_docker_container = bridge_docker.containers
container_ip_list = []

#Disconnect all containers from the docker0 bridge and connect them to the ovs bridge

for i in bridge_docker_container:
    attributes = i.attrs
    name = str(attributes["Name"])
    name = name[1:]
    ip_bridge_docker = str(attributes["NetworkSettings"]["Networks"]["bridge"]["IPAddress"])
    bridge_ovs.connect(name)
    ip_bridge_ovs = str(i.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"])
    container_ip_list.append((name, ip_bridge_docker, ip_bridge_ovs))
    
ovs_bridge_name = rf.get_ovs_bridge_name()
if ovs_bridge_name is None:
    raise NameError("no ovs bridge found")
print ovs_bridge_name



    