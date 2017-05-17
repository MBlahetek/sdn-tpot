'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
from threading import Timer
import os
import time
import datetime
import json
import docker
import static_entry_pusher
import rest_api_getter


class LogMonitor(object):
    
    def __init__(self, controller_ip, period, threshold):
        self.controller = controller_ip
        self.switch = switch
        self.period = period
        self.threshold = threshold
        self.flow_entry_pusher = static_entry_pusher.StaticEntryPusher(self.controller)
        self.last_log_entry = []
        self.blacklist_candidates = []

    def get_existing_ids_log_path(self):
        ids_dirs = []
        log_dirs = [name for name in os.listdir("/data/") if os.path.isdir(os.path.join("/data/", name))]
        for dirname in log_dirs:
            if "suricata_" in dirname:
                ids_dirs.append(dirname)
        return ids_dirs
    
    def block_ip(self, ip):
        flow_name = "blacklisted: " + ip
        
        block_flow = {
            'switch': self.switch,
            "name": flow_name,
            "cookie":"0",
            "priority":"32768",
            "in_port":"local",
            "eth_type":"0x0800",
            "ipv4_src": ip,
            "ipv4_dst":"0.0.0.0/0",
            "active":"true",
            "idle_timeout":"43200", # half day
            "hard_timeout":"172800", # two days
            "actions":""
        }
            
        self.flow_entry_pusher.set(block_flow)

    def check_logs(self):
        ids_dirs = get_existing_ids_log_path()
        # check if there are already any log directories
        if ids_dirs:
            # check logs of each ids
            for ids in ids_dirs:
                # check if the ids is new
                new_ids_dir = True
                for entry in self.last_log_entry:
                    if ids == entry[0]:
                        new_ids_dir = False
                        last_log = entry[1]
                        break
                # open json log
                log_data = []                      
                with open("/data/" + ids + "/log/eve.json") as json_file:    
                    for line in json_file:
                        log_data.append(json.loads(line))
                    for log in log_data:
                        json_timestamp = log["timestamp"][:-5]
                        timestamp = datetime.strptime(json_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                        # if new ids check all logs
                        # otherwise check timestamp
                        if new_ids_dir or timestamp > last_log:
                            event_type = log["event_type"]
                            src_ip = log["src_ip"]
                            if event_type == "alert":
                                # check if blacklist empty
                                if self.blacklist_candidates:
                                    # increase blacklist counter
                                    for ip in self.blacklist_candidates:
                                        if ip[0] == src_ip:
                                            ip[1] += ip[1]
                                            break
                                else:
                                    self.blacklist_candidates.append([src_ip, 1])
                # save last timestamp for the next cycle
                if not new_ids_dir:
                    for entry in self.last_log_entry:
                        if ids == entry[0]:
                            entry[1] = timestamp
                else:
                    self.last_log_entry.append([ids, timestamp])
        # check blacklist counter
        temp_blacklist_candidates = self.blacklist_candidates
        for ip in temp_blacklist_candidates:
            if ip[1] > self.threshold:
                block_ip(ip[0])
                self.blacklist_candidates.remove([ip[0], ip[1]])
                     
    def cycle(self):
        cycles_per_day = 864000 /self.period
        i = 0
        while True:
            cycle = Timer(self.period, check_logs)
            cycle.start()
            i += 1
            if i > cycles_per_day:
                self.blacklist_candidates = []
                i = 0

client = docker.from_env()
floodlight = client.containers.get("floodlight")
controller_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
rest_api = rest_api_getter.RestApiGetter(controller_ip)
switch_id = rest_api.get_switch()

period = 1800 # seconds => 1800 = 30 minutes
threshold = 3 # alerts threshold per day

monitor = LogMonitor(controller_ip, period, threshold)
monitor.cycle()