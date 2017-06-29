'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
from threading import Timer
from datetime import datetime
import os
import time
import json
import docker
import logging
import static_entry_pusher
import rest_api_getter

logging.basicConfig(filename='log_monitor.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt="%Y-%m-%dT%H:%M:%S")

class LogMonitor(object):
    
    def __init__(self, controller, switch, period, threshold, soft_ban_time, hard_ban_time):
        self.controller = controller
        self.switch = switch
        self.period = period
        self.threshold = threshold
        self.soft_ban_time = str(soft_ban_time)
        self.hard_ban_time = str(hard_ban_time)
        self.flow_entry_pusher = static_entry_pusher.StaticEntryPusher(self.controller)
        self.last_log_entry = []
        self.last_log_cowrie = None
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
            "idle_timeout": self.soft_ban_time, 
            "hard_timeout": self.hard_ban_time,
            "actions":""
        }
            
        self.flow_entry_pusher.set(block_flow)
        logging.info("blacklisted: " + ip)
    
    def increment_blacklist_counter(self, ip, value):
        if self.blacklist_candidates:
            # increase blacklist counter
            for candidate in self.blacklist_candidates: 
                if candidate[0] == ip:
                    candidate[1] += value
                    logging.info("increment blacklist counter of ip: " + candidate[0] + " (now: " + str(candidate[1]) + ")") 
                    break
        else:
            self.blacklist_candidates.append([ip, value])
            logging.info("increment blacklist counter of ip: " + ip + " (now: 1)")      

    def check_logs(self):
        ids_dirs = self.get_existing_ids_log_path()
        timestamp = None
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
                                self.increment_blacklist_counter(src_ip, self.threshold)
                # save last timestamp for the next cycle
                if not new_ids_dir:
                    for entry in self.last_log_entry:
                        if ids == entry[0]:
                            entry[1] = timestamp
                else:
                    if timestamp is not None:
                        self.last_log_entry.append([ids, timestamp])
        log_data = []
        timestamp = None
        with open("/data/cowrie/log/cowrie.json") as json_file:    
            for line in json_file:
                log_data.append(json.loads(line))
            for log in log_data:                        
                json_timestamp = log["timestamp"][:-1]
                timestamp = datetime.strptime(json_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                if self.last_log_cowrie is None or timestamp > self.last_log_cowrie:
                    event_type = log["eventid"]
                    src_ip = log["src_ip"]
                    if event_type == "cowrie.login.failed":
                        username = log["username"]
                        password = log["password"]
                        logging.info("login failed | ip: " + src_ip + " | username: " + username + " | password: " + password)
                        self.increment_blacklist_counter(src_ip, 1)
                    if event_type == "cowrie.login.success":
                        username = log["username"]
                        password = log["password"]
                        logging.info("login succeded | ip: " + src_ip + " | username: " + username + " | password: " + password)
                        self.increment_blacklist_counter(src_ip, self.threshold)
        self.last_log_cowrie = timestamp
        # check blacklist counter
        temp_blacklist_candidates = self.blacklist_candidates
        for ip in temp_blacklist_candidates:
            if ip[1] > self.threshold:
                self.block_ip(ip[0])
                self.blacklist_candidates.remove([ip[0], ip[1]])
                     
    def cycle(self):
        cycles_per_day = 864000 /self.period
        i = 0
        while True:
            self.check_logs() 
            i += 1
            if i > cycles_per_day:
                self.blacklist_candidates = []
                i = 0
            time.sleep(self.period)  

client = docker.from_env()
floodlight = client.containers.get("floodlight")
controller_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
rest_api = rest_api_getter.RestApiGetter(controller_ip)
switch_id = rest_api.get_switch()

period = 300 # seconds 
threshold = 5 # suricata alert = 5 ; failed login = 1
soft_ban = 600 # seconds 
hard_ban = 172.800 # seconds 

monitor = LogMonitor(controller_ip, switch_id, period, threshold, soft_ban, hard_ban)
monitor.cycle()