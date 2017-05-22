'''
Created on 28.04.2017

@author: Matthias Blahetek
'''
import static_entry_pusher
import rest_api_getter
import docker
import time

client = docker.from_env()
floodlight = client.containers.get("floodlight")
glastopf = client.containers.get("glastopf")
cowrie = client.containers.get("cowrie")
floodlight_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
glastopf_ip = glastopf.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
cowrie_ip = cowrie.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]

bridge_ovs = client.networks.list('sdnnet')[0]
k = 2
for i in bridge_ovs.containers:
    cmd_str = "ping -c 3 172.18.0." + str(k)
    print cmd_str + "..."
    cowrie.exec_run(cmd_str)
    k += 1   
# give floodlight few seconds to update its database
# otherwise the swith port mapping in the next step probably fails.
time.sleep(3)
# get ip - switch port - mapping for dynamic pro-activ flow generation
print "get switch ports for each container..."
rest_api = rest_api_getter.RestApiGetter(floodlight_ip)
ip_port_map = rest_api.get_ip_port_mapping()
print "get switch id..."
try:
    switch = rest_api.get_switch()
except (UnboundLocalError, IndexError):
    print "no switch id found"
    quit()
for i in ip_port_map:
    if i[0] == glastopf_ip:
        glastopf_port = i[1]
    elif i[0] == cowrie_ip:
        cowrie_port = i[1]
    elif i[0] == floodlight_ip:
        floodlight_port = i[1]
# write all the pro-active flow rules
print "loading pro-active flow rules..."
flows = []

ovs_bridge = {
    'switch': switch,
    "name":"ovs_bridge",
    "cookie":"0",
    "priority":"11000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ipv4_src":"172.18.0.0/16",
    "ipv4_dst": "172.18.0.0/16",
    "active":"true",
    "actions":"output=flood"
    }
flows.append(ovs_bridge)

floodlight_rest = {
    'switch': switch,
    "name":"floodlight_rest",
    "cookie":"0",
    "priority":"14000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0", # TODO restrict on admin ip range
    "ipv4_dst": floodlight_ip + "/32",
    "tcp_dst":"9090",
    "active":"true",
    "actions":"output=" + floodlight_port
    }
flows.append(floodlight_rest)

floodlight_drop = {
    'switch': switch,
    "name":"floodlight_drop",
    "cookie":"0",
    "priority":"1000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": floodlight_ip + "/32",
    "active":"true",
    "actions":""
    }
flows.append(floodlight_drop)

glastopf_http = {
    'switch': switch,
    "name":"glastopf_http",
    "cookie":"0",
    "priority":"15000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": glastopf_ip + "/32",
    "tcp_dst":"80",
    "active":"true",
    "actions":"output=" + glastopf_port
    }
flows.append(glastopf_http)

glastopf_drop = {
    'switch': switch,
    "name":"glastopf_drop",
    "cookie":"0",
    "priority":"1000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": glastopf_ip + "/32",
    "active":"true",
    "actions":""
    }
flows.append(glastopf_drop)
 
cowrie_ssh = {
    'switch': switch,
    "name":"cowrie_ssh",
    "cookie":"0",
    "priority":"15000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": cowrie_ip + "/32",
    "tcp_dst":"2222",
    "active":"true",
    "actions":"output=" + cowrie_port
    }
flows.append(cowrie_ssh)
 
cowrie_telnet = {
    'switch': switch,
    "name":"cowrie_telnet",
    "cookie":"0",
    "priority":"15000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": cowrie_ip + "/32",
    "tcp_dst":"2223",
    "active":"true",
    "actions":"output=" + cowrie_port
    }
flows.append(cowrie_telnet)

cowrie_drop = {
    'switch': switch,
    "name":"cowrie_drop",
    "cookie":"0",
    "priority":"1000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": cowrie_ip + "/32",
    "active":"true",
    "actions":""
    }
flows.append(cowrie_drop)
# send the pro-activ flow rules to the controller
push = static_entry_pusher.StaticEntryPusher(floodlight_ip)
for flow in flows:
    push.set(flow)
    flow_id = flow["name"]
    print "flow entry set: " + flow_id