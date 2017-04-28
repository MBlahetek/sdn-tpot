'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker
import reconffunctions as rf



client = docker.from_env()

bridge_docker = client.networks.list('bridge')[0]
bridge_docker_container = bridge_docker.containers

for i in bridge_docker_container:
    attributes = i.attrs
    name = attributes["Name"]
    name = name[1:]
    ip = attributes["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
    
    break
