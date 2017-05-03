# sdn-tpot

Intsallationsschritte:

modprobe openvswitch
pip install --upgrade python-iptables
apt-get install docker-compose
cd sdn-tpot/main/
docker-compose up -d
/bin/bash ./setup_sdn_tpot