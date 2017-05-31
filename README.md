# sdn-tpot



## Getting Started


### Prerequisites


```
cd ..
git clone https://github.com/MBlahetek/sdn-tpot.git
modprobe openvswitch
apt-get install docker-compose
cd sdn-tpot/main/
docker-compose up -d
pip install --upgrade python-iptables
pip install docker
docker pull mblahetek/suricata
```

### Installing

```
docker network create -d ovs sdnnet
docker run -d -p 6653:6653 -p 9090:9090 --name=floodlight --net=bridge mblahetek/floodlight
cp crontab /etc/
service elk stop
python ../reconfigure/reconfigure.py
service elk start
service ui-for-docker start
service netdata start
python ../scripts/static_flows.py
python ../scripts/tpot_monitor.py &
python ../scripts/log_monitor.py &
```

