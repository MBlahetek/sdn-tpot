'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import docker

client = docker.from_environment()

client.container.list()