'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker
client = docker.from_env()
for container in client.containers.list():
  print container.id