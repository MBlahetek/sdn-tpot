'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
import rest_api_getter
import static_entry_pusher
import json
import docker
import time

class TpotMonitor(object):
    
    def __init__(self, controller, switch, polling):
        self.controller = controller
        self.switch = switch
        self.polling = polling
        self.rest_api = rest_api_getter.RestApiGetter(self.controller)
        self.flow_stats_path = "/wm/core/switch/" + self.switch + "/flow/json"
        
    def get_flows(self):
        json_object = self.rest_api.get(self.flow_stats_path)
        json_flows = json_object["flows"]
        return json_flows
    
    def add_ids(self, flow):
        raise NotImplementedError("TODO")
  
    def remove_ids(self, flow):
        raise NotImplementedError("TODO")
        
    def cycle(self):
        old_stats = []
        print "getting first package counts..."
        json_flows = self.get_flows()
        for flow in json_flows:
            if int(flow["priority"]) > 1000:
                package_count = int(flow["packet_count"])
                old_stats.append([flow["match"], flow["priority"], package_count, 0])
                
        time.sleep(self.polling)
                
        while 1:
            print "monitoring flows for packet increasement..."
            json_flows = self.get_flows()
            for flow in json_flows:
                if int(flow["priority"]) > 1000 and int(flow["priority"]) <= 32700:
                    new_flow = False
                    package_count = int(flow["packet_count"])
                    for i in old_stats:                    
                        if flow["match"] == i[0] and flow["priority"] == i[1]:
                            old_count = i[2]
                            old_package_increase = i[3]
                            new_package_increase = package_count - old_count
                            if new_package_increase != 0 and int(flow["priority"]) == 15000: # inital traffic causes start of a specific ids
                                self.add_ids(flow)
                            i[2] = package_count
                            i[3] = new_package_increase
                            new_flow = False
                            break
                        else:
                            new_flow = True
                    if new_flow:
                        old_stats.append([flow["match"], flow["priority"], package_count, 0])
            time.sleep(self.polling)
            
client = docker.from_env()
floodlight = client.containers.get("floodlight")
controller_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
rest_api = rest_api_getter.RestApiGetter(controller_ip)
switch_id = rest_api.get_switch()

polling = 15     

monitor = TpotMonitor(controller_ip, switch_id, polling)
DosMitigation.cycle()