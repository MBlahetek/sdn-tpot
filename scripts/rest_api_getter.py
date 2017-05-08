import httplib
import json
 
class RestApiGetter(object):
 
    def __init__(self, server):
        self.server = server
 
    def get(self, path):
        ret = self.rest_call(path, 'GET')
        return json.loads(ret[2])    

    def get_switch(self):
        path = "/wm/device"
        ret = self.rest_call(path, 'GET')
        json_object = json.loads(ret[2])
        for entity in json_object["devices"]:
            if entity["ipv4"] == ["172.18.0.1"]:
                switch = entity["attachmentPoint"][0]["switch"]
                break
        return switch  

    def rest_call(self, path, action):
        conn = httplib.HTTPConnection(self.server, 9090)
        conn.request(action, path)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret