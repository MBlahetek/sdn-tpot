'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
import rest_api_getter
import static_entry_pusher
import json
import docker
import time
import os
import logging

logging.basicConfig(filename='tpot_monitor.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt="%Y-%m-%dT%H:%M:%S")

PORTS = {
    "2222":"ssh",
    "2223":"telnet",
    "80":"http"   
    }

class TpotMonitor(object):
    
    def __init__(self, controller, switch, polling, ids_standby):
        self.controller = controller
        self.switch = switch
        self.polling = polling
        self.ids_standby = ids_standby / polling
        self.ids_container = []
        self.rest_api = rest_api_getter.RestApiGetter(self.controller)
        self.flow_stats_path = "/wm/core/switch/" + self.switch + "/flow/json"
        
    def get_flows(self):
        json_object = self.rest_api.get(self.flow_stats_path)
        json_flows = json_object["flows"]
        return json_flows
    
    def add_ids(self, flow):
        new_priority = int(flow["priority"]) + 100
        in_port = flow["match"]["in_port"]
        eth_type = flow["match"]["eth_type"]
        ip_proto = flow["match"]["ip_proto"]
        ipv4_dst = flow["match"]["ipv4_dst"]
        tcp_dst = flow["match"]["tcp_dst"]
        actions = flow["instructions"]["instruction_apply_actions"]["actions"]
        
        name = "suricata_" + PORTS[tcp_dst]
        client = docker.from_env()
        if name in self.ids_container:
            suricata = client.containers.get(name)
            suricata.start()
            suricata = client.containers.get(name)
        else:
            log_path = '/data/' + name + "/"
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            container = client.containers.run('dtagdevsec/suricata:latest1610', 
                                            detach=True,
                                            name=name,
                                            cap_add=["NET_ADMIN"],
                                            network_mode="sdnnet",
                                            privileged=True,
                                            volumes={ log_path : {'bind':'/data/suricata' , 'mode': 'rw'}})
            suricata = client.containers.get(name)
            suricata.exec_run("mkdir /data/suricata/log")
            self.ids_container.append(name)
        print "docker container started: " + name
        logging.info("docker container started: " + name)
        suricata.exec_run("ifconfig eth0 promisc")
        suricata.exec_run(cmd="/usr/bin/suricata -c /etc/suricata/suricata.yaml -S \"/etc/suricata/rules/*.rules\" -i eth0", detach=True)
        time.sleep(3)
        suricata.exec_run("ping -c 3 172.18.0.1")
        suricata_ip = suricata.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
        ip_port_map = self.rest_api.get_ip_port_mapping()
        for i in ip_port_map:
            if i[0] == suricata_ip:
                container_switch_port = i[1]
                break
        actions = actions + ",output=" + container_switch_port
        
        ids_flow = {
            'switch': self.switch,
            "name": name,
            "cookie":"0",
            "priority": str(new_priority),
            "in_port": in_port,
            "eth_type": eth_type,
            "ip_proto":ip_proto,
            "ipv4_src":"0.0.0.0/0",
            "ipv4_dst": ipv4_dst,
            "tcp_dst": tcp_dst,
            "active":"true",
            "actions": actions
            }
        
        push = static_entry_pusher.StaticEntryPusher(self.controller)
        push.set(ids_flow)
        logging.info("flow entry set: " + name)
        print "flow entry set: " + name
        
    def remove_ids(self, flow):
        tcp_dst = flow["match"]["tcp_dst"]
        name = "suricata_" + PORTS[tcp_dst]
        ids_flow = {"name": name}
        push = static_entry_pusher.StaticEntryPusher(self.controller)
        push.remove(ids_flow)
        print "flow entry removed: " + name
        logging.info("flow entry removed: " + name)
        client = docker.from_env()
        suricata = client.containers.get(name)
        suricata.stop()
        print "docker container stopped: " + name
        logging.info("docker container stopped: " + name)
        
    def cycle(self):
        logging.info("TPot-Monitor started...")
        old_stats = []        
        ids_active = []
                
        while 1:
            json_flows = self.get_flows()
            for flow in json_flows:
                if int(flow["priority"]) > 1000 and int(flow["priority"]) <= 32700:
                    package_count = int(flow["packet_count"])
                    new_flow = True
                    
                    for i in old_stats:                    
                        if flow["match"] == i[0] and flow["priority"] == i[1]:
                            old_count = i[2]
                            old_package_increase = i[3]
                            new_package_increase = package_count - old_count
                            # inital traffic causes start of a specific ids
                            if new_package_increase > 0 and int(flow["priority"]) == 15000 and flow["match"] not in ids_active:
                                self.add_ids(flow)
                                ids_active.append(flow["match"])
                            # if there's no traffic over the last k polling intervalls, the ids + flow will be removed
                            if new_package_increase == 0 and int(flow["priority"]) == 15100:
                                if len(i) == 4:
                                    k = 1
                                    i.append(k)
                                else:
                                    i[4] += 1
                                    if i[4] == self.ids_standby:
                                        self.remove_ids(flow)
                                        del i[4]
                                        ids_active.remove(flow["match"])
                            if new_package_increase != 0 and int(flow["priority"]) == 15100 and len(i) == 5:
                                del i[4]
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

polling = 5 # check flow packet statistics every n seconds
ids_standby = 300 # active standby without traffic in seconds

monitor = TpotMonitor(controller_ip, switch_id, polling, ids_standby)
monitor.cycle()