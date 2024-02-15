lxc-attach -n R01 -- ip addr add 10.0.0.129/26 dev eth0 && ip link set eth0 up
lxc-attach -n R01 -- ip addr add 10.0.0.193/27 dev eth1 && ip link set eth1 up
lxc-attach -n R01 -- ip addr add 10.0.0.225/28 dev eth2 && ip link set eth2 up
lxc-attach -n R02 -- ip addr add 10.0.0.226/28 dev eth0 && ip link set eth0 up
lxc-attach -n R02 -- ip addr add 10.0.0.241/29 dev eth1 && ip link set eth1 up
lxc-attach -n R02 -- ip addr add 10.0.0.249/29 dev eth2 && ip link set eth2 up
lxc-attach -n R03 -- ip addr add 10.0.0.242/29 dev eth0 && ip link set eth0 up
lxc-attach -n R05 -- ip addr add 10.0.0.249/30 dev eth0 && ip link set eth0 up