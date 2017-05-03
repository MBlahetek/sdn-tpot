import os
import json
import time

polling = 60
threshold = 3
margin = 100
controller_id = "10.10.1.10:8080"      #TODO
switch_id = "00:02:14:58:d0:ad:e4:80"  #TODO

old_stats = []
old_package_increase = []

flow_stats = "curl http://" + controller_id + "/wm/core/switch/" 
+ switch_id + "/flow/json"

json_file = os.popen(flow_stats).read()
json_object = json.loads(json_file)
json_flows = json_object["flows"]

for i in range(len(json_flows)):
    package_count = int(json_flows[i]["packetCount"])
    old_stats.append(package_count)
    
time.sleep(polling)

json_file = os.popen(flow_stats).read()
json_object = json.loads(json_file)
json_flows = json_object["flows"]

for i in range(len(json_flows)):
    package_count = int(json_flows[i]["packetCount"])
    package_increase = package_count - old_stats[i]
    old_package_increase.append(package_increase)
    old_stats[i] = package_count
    
time.sleep(polling)

while 1:
    
    json_file = os.popen(flow_stats).read()
    json_object = json.loads(json_file)
    json_flows = json_object["flows"]
    
    k = 0    
    
    for i in range(len(json_flows)):
        
        if json_flows[i]["priority"] == "500":
            old_count = old_stats[k]
            package_count = int(json_flows[i]["packetCount"])
            new_package_increase = package_count - old_count
                        
            if ((old_package_increase[k] * threshold) < new_package_increase) and (new_package_increase[k] > margin):
                                        
                json_match = json_flows[i]["match"]
                ip_src = json_match["ipv4_src"]
                ip_dest = json_match["ipv4_dst"]
                temp_flow_name = "DoS_Mitigation_" + str(k)
                
                new_temp_flow = "curl -d '{\"switch\": \"" + switch_id + "\", \"name\":\"" + temp_flow_name + "\", \"eth_type\":\"0x0800\", \"priority\":\"2000\", \"ipv4_src\":\"" + ip_src + "\", \"ipv4_dst\":\"" + ip_dest + "\", \"active\":\"true\",  \"actions\":\"\", \"hard_timeout\":\"300\"}' http://" + controller_id + "/wm/staticflowpusher/json"
 
                push_new_flow = os.popen(new_temp_flow)
                print(push_new_flow)
            
            old_package_increase[k] = new_package_increase    
            old_stats[k] = package_count
            
            k = k + 1
                
    time.sleep(polling)