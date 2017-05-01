'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

def get_ovs_bridge_name():
    try:
        for line in open('/proc/net/dev', 'r'):
            if "ovsbr" in line:
                bridge_name = line.split(":", 1)[0]
                return bridge_name
    finally:
        bridge_name = None
        return bridge_name
        