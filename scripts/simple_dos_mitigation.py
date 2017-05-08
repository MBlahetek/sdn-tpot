from threading import Thread
import rest_api_getter
import static_entry_pusher
import os
import json
import time
import docker
from pickle import FALSE

"""
TODO take care of flow mapping
"""

class SimpleDosMitigation(object):
    
    def __init__(self, controller, switch, polling, threshold, margin):
        self.controller = controller
        self.switch = switch
        self.polling = polling
        self.threshold = threshold
        self.margin = margin
        self.rest_api = rest_api_getter.RestApiGetter(self.controller)
        self.flow_stats_path = "/wm/core/switch/" + self.switch + "/flow/json"
        
    def get_flows(self):
        json_object = self.rest_api.get(self.flow_stats_path)
        json_flows = json_object["flows"]
        return json_flows
    
    def mitigation(self, flow, index):
        json_match = flow["match"]
        if "ip4_src" in json_match:
            ip_src = json_match["ipv4_src"]
        if "ipv4_dst" in json_match:
            ip_dest = json_match["ipv4_dst"]
        temp_flow_name = "DoS_Mitigation_" + str(index)
        new_temp_flow = {
            'switch': self.switch,
            "name": temp_flow_name,
            "cookie":"0",
            "priority":"32768",
            "in_port":"local",
            "eth_type":"0x0800",
            "ipv4_src": ip_src,
            "ipv4_dst": ip_dest,
            "active":"true",
            "hard_timeout":"300",
            "actions":""
        }
        push = static_entry_pusher.StaticEntryPusher(self.controller)
        push.set(new_temp_flow)
        print "flow entry set: " + temp_flow_name
        
    def cycle(self):        
        old_stats = []
        old_package_increase = []
        
        print "getting first package counts..."
        json_flows = self.get_flows()
        for flow in json_flows:
            if int(flow["priority"]) > 1000:
                package_count = int(flow["packet_count"])
                old_stats.append([flow["match"], flow["priority"], package_count, 0])
        
        time.sleep(polling)
        
        print "calculating first increasement values..."
        json_flows = self.get_flows()
        for flow in json_flows:
            if int(flow["priority"]) > 1000:
                new_flow = False
                package_count = int(flow["packet_count"])
                for i in old_stats:
                    if flow["match"] == i[0] and flow["priority"] == i[1]:
                        package_increase = package_count - i[2]
                        i[2] = package_count
                        i[3] = package_increase
                        new_flow = False
                        break
                    else:
                        new_flow = True
                if new_flow:
                    old_stats.append([flow["match"], flow["priority"], package_count, 0])
                  
        time.sleep(polling)
        
        while 1:
            print "monitoring flows for suspicious packet increasement..."
            json_flows = self.get_flows()
            for flow in json_flows:
                if int(flow["priority"]) >= 1000 and int(flow["priority"]) <= 32700:
                    new_flow = False
                    package_count = int(flow["packet_count"])
                    k = 0
                    for i in old_stats:                    
                        if flow["match"] == i[0] and flow["priority"] == i[1]:
                            old_count = i[2]
                            old_package_increase = i[3]
                            new_package_increase = package_count - old_count
                            if ((old_package_increase * threshold) < new_package_increase) and (new_package_increase > margin):
                                self.mitigation(flow, k)
                            i[2] = package_count
                            i[3] = new_package_increase
                            new_flow = False
                            break
                        else:
                            new_flow = True
                        k += 1
                    if new_flow:
                        old_stats.append([flow["match"], flow["priority"], package_count, 0])
            time.sleep(polling)


client = docker.from_env()
floodlight = client.containers.get("floodlight")
controller_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
rest_api = rest_api_getter.RestApiGetter(controller_ip)
switch_id = rest_api.get_switch()

polling = 30
threshold = 5
margin = 1000      

DosMitigation = SimpleDosMitigation(controller_ip, switch_id, polling, threshold, margin)
DosMitigation.cycle()