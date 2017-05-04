import static_entry_pusher as pusher
import docker

"""
TODO get ip/switch-port mapping via: curl http://172.18.0.5:9090/wm/device/
TODO docker exec ping for making them visible
"""

client = docker.from_env()
floodlight = client.containers.get("floodlight")
glastopf = client.containers.get("glastopf")
cowrie = client.containers.get("cowrie")
floodlight_ip = floodlight.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
glastopf_ip = glastopf.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]
cowrie_ip = cowrie.attrs["NetworkSettings"]["Networks"]["sdnnet"]["IPAddress"]

push = pusher.StaticEntryPusher(floodlight_ip)
flows = []

glastopf_http = {
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"glastopf_http",
    "cookie":"0",
    "priority":"30000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": glastopf_ip + "/32",
    "tcp_dst":"80",
    "active":"true",
    "actions":"output=3"
    }
flows.append(glastopf_http)

glastopf_drop = {
    'switch':"00:00:42:41:c8:da:11:40",
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
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"cowrie_ssh",
    "cookie":"0",
    "priority":"30000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": cowrie_ip + "/32",
    "tcp_dst":"2222",
    "active":"true",
    "actions":"output=3"
    }
flows.append(cowrie_ssh)
 
cowrie_telnet = {
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"cowrie_telnet",
    "cookie":"0",
    "priority":"30000",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst": cowrie_ip + "/32",
    "tcp_dst":"2223",
    "active":"true",
    "actions":"output=3"
    }
flows.append(cowrie_telnet)

cowrie_drop = {
    'switch':"00:00:42:41:c8:da:11:40",
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

for flow in flows:
    push.set(flow)
    flow_id = flow["name"]
    print "flow entry set: " + flow_id