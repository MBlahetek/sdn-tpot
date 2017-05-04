import httplib
import json
 
class StaticEntryPusher(object):
 
    def __init__(self, server):
        self.server = server
 
    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])
 
    def set(self, data):
        ret = self.rest_call(data, 'POST')
        return ret[0] == 200
 
    def remove(self, objtype, data):
        ret = self.rest_call(data, 'DELETE')
        return ret[0] == 200
 
    def rest_call(self, data, action):
        path = '/wm/staticentrypusher/json'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 9090)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret
 
pusher = StaticEntryPusher('172.18.0.5')
 
cowrie_ssh = {
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"cowrie_ssh",
    "cookie":"0",
    "priority":"32768",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst":"172.18.0.4/32",
    "tcp_dst":"2222",
    "active":"true",
    "actions":"output=3"
    }
 
cowrie_telnet = {
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"cowrie_ssh",
    "cookie":"0",
    "priority":"32768",
    "in_port":"local",
    "eth_type":"0x0800",
    "ip_proto":"0x06",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst":"172.18.0.4/32",
    "tcp_dst":"2223",
    "active":"true",
    "actions":"output=3"
    }

cowrie_drop = {
    'switch':"00:00:42:41:c8:da:11:40",
    "name":"cowrie_drop",
    "cookie":"0",
    "priority":"32768",
    "in_port":"local",
    "eth_type":"0x0800",
    "ipv4_src":"0.0.0.0/0",
    "ipv4_dst":"172.18.0.4/32",
    "active":"true",
    "actions":""
    }
 
pusher.set(cowrie_ssh)
pusher.set(cowrie_telnet)
pusher.set(cowrie_drop)