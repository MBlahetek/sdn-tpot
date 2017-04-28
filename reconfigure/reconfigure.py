'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker

client = docker.from_env()

bridge_docker = client.networks.list('bridge')[0]
bridge_docker_container = bridge_docker.containers

print bridge_docker_container[0].attrs