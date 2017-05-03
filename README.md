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
/bin/bash ./setup_sdn_tpot
```

