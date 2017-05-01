'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker
import reconffunctions as rf

client = docker.from_env()

bridge_docker = client.networks.list('bridge')[0]
bridge_docker_container = bridge_docker.containers
container_list = []

for i in bridge_docker_container:
    attributes = i.attrs
    name = str(attributes["Name"])
    name = name[1:]
    ip = str(attributes["NetworkSettings"]["Networks"]["bridge"]["IPAddress"])
    container_list.append((name, ip))
    
ovs_bridge_name = rf.get_ovs_bridge_name
if ovs_bridge_name is None:
    raise "no ovs bridge found"
print ovs_bridge_name

    