# sdn-tpot



## Getting Started


### Prerequisites


```
cd ..
git clone https://github.com/MBlahetek/sdn-tpot.git
modprobe openvswitch
apt-get install docker-compose
cd sdn-tpot/main/
cp crontab /etc/crontab
docker-compose up -d
pip install --upgrade python-iptables
pip install docker
```

### Installing

```
docker network create -d ovs sdnnet
docker run -d -v /data:/home/hostdata -p 6653:6653 -p 9090:9090 --name=floodlight --net=bridge bladdl/floodlight
/bin/bash ./setup_sdn_tpot
```

