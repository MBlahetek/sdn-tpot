'''
Created on 28.04.2017

@author: Matthias Blahetek
'''

import iptc

def get_ovs_bridge_name():
    for line in open('/proc/net/dev', 'r'):
        if "ovsbr" in line:
            bridge_name = line.split(":", 1)[0]
            return str(bridge_name)

def update_iptables_chain(chain, ip_map, ovs_bridge_name):
    rules = chain.rules
    number = len(rules)
    counter = 1
    new_rules = []
    
    for r in rules:
        new_rule = iptc.Rule()
        
        if r.matches:
            match = r.matches[0]
            new_rule.add_match(match)
            
        if r.in_interface is not None:
            if r.in_interface == "docker0":
                new_rule.in_interface = ovs_bridge_name
            elif r.in_interface == "!docker0":
                new_rule.in_interface = "!" + ovs_bridge_name
        if r.out_interface is not None:
            if r.out_interface == "docker0":
                new_rule.out_interface = ovs_bridge_name
            elif r.out_interface == "!docker0":
                new_rule.out_interface = "!" + ovs_bridge_name
        
        if r.src == "172.17.0.0/255.255.0.0":
            new_rule.src = "172.18.0.0/255.255.0.0" 
        elif r.src != "0.0.0.0/0.0.0.0":
            old_ip = r.src.split("/", 1)[0]
            old_subnetmask = r.src.split("/", 1)[1]
            for ip in ip_map:
                if ip[1] == old_ip:
                    new_rule.src = ip[2] + "/" + old_subnetmask
                    break
        else:
            new_rule.src = "0.0.0.0/0.0.0.0"
                
        if r.dst == "172.17.0.0/255.255.0.0":
            new_rule.dst = "172.18.0.0/255.255.0.0" 
        elif r.dst != "0.0.0.0/0.0.0.0":
            old_ip = r.dst.split("/", 1)[0]
            old_subnetmask = r.dst.split("/", 1)[1]
            for ip in ip_map:
                if ip[1] == old_ip:
                    new_rule.dst = ip[2] + "/" + old_subnetmask
                    break
        else:
            new_rule.dst = "0.0.0.0/0.0.0.0"
        
        new_rule.protocol = r.protocol
        
        new_rule.target = r.target
           
        new_rules.append(new_rule)
        
        print "      created rule " + counter + " of " + number
        counter += 1
    
    for r in rules:
        chain.delete_rule(r)
    
    counter = 1
    for r in new_rules:
        chain.append_rule(r)
        print "      updated rule " + counter + " of " + number
        counter += 1