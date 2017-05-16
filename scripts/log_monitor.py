'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
from threading import Timer
import os
import time
import datetime
import json
import static_entry_pusher
import docker

class LogMonitor(object):
    
    def __init__(self, controller_ip, period, threshold):
        self.controller = controller_ip
        self.switch = switch
        self.period = period
        self.threshold = threshold
        self.flow_entry_pusher = static_entry_pusher.StaticEntryPusher(self.controller)
        self.last_log_entry = []

    def get_existing_ids_log_path(self):
        ids_dirs = []
        log_dirs = [name for name in os.listdir("/data/") if os.path.isdir(os.path.join("/data/", name))]
        for dirname in log_dirs:
            if "suricata_" in dirname:
                ids_dirs.append(dirname)
        return ids_dirs

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
                        if new_ids_dir or timestamp > last_log:
                            # Magie: SrcIP der allerts zählen und ggf blacklisten
                            raise NotImplementedError
                if not new_ids_dir:
                    
                    print timestamp
                    
                        
        
        
    def cycle(self):
        while True:
            cycle = Timer(self.period, check_logs)
            cycle.start()