#!/usr/bin/python3
import os
import sys
import tqdm
from tqdm import tqdm

'''
Example of the starting configuration file:
# Template used to create this container: /usr/share/lxc/templates/lxc-download
# Parameters passed to the template: -d ubuntu -r bionic -a amd64
# Template script checksum (SHA-1): 9748088977ba845f625e45659f305a5395c2dc7b
# For additional config options, please look at lxc.container.conf(5)
# Uncomment the following line to support nesting containers:
#lxc.include = /usr/share/lxc/config/nesting.conf
# (Be aware this has security implications)
# Distribution configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf
lxc.arch = linux64
# Container specific configuration
lxc.rootfs = /var/lib/lxc/R01/rootfs
lxc.rootfs.backend = dir
lxc.utsname = R01
# Network configuration
lxc.network.type = veth
lxc.network.link = br01
lxc.network.flags = up
lxc.network.name = eth0
lxc.network.veth.pair = R01-eth0 

lxc.network.type = veth
lxc.network.link = br02
lxc.network.flags = up
lxc.network.name = eth1
lxc.network.veth.pair = R01-eth1 

lxc.network.type = veth
lxc.network.link = br03
lxc.network.flags = up
lxc.network.name = eth2
lxc.network.veth.pair = R01-eth2

Example of the ending configuration file:
# Template used to create this container: /usr/share/lxc/templates/lxc-download
# Parameters passed to the template: -d ubuntu -r bionic -a amd64
# Template script checksum (SHA-1): 9748088977ba845f625e45659f305a5395c2dc7b
# For additional config options, please look at lxc.container.conf(5)
# Uncomment the following line to support nesting containers:
#lxc.include = /usr/share/lxc/config/nesting.conf
# (Be aware this has security implications)
# Distribution configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf
lxc.arch = linux64
# Container specific configuration
lxc.rootfs.path = dir:/var/lib/lxc/R01/rootfs
#lxc.rootfs.backend = dir
lxc.uts.name = R01
# Network configuration
lxc.net.0.type = veth
lxc.net.0.link = br01
lxc.net.0.flags = up
lxc.net.0.name = eth0
lxc.net.0.veth.pair = R01-eth0 

lxc.net.1.type = veth
lxc.net.1.link = br02
lxc.net.1.flags = up
lxc.net.1.name = eth1
lxc.net.1.veth.pair = R01-eth1 

lxc.net.2.type = veth
lxc.net.2.link = br03
lxc.net.2.flags = up
lxc.net.2.name = eth2
lxc.net.2.veth.pair = R01-eth2
'''

def update_network_configs(text):
    netsect=text.split('# Network configuration')[1]
    netdevs=netsect.split('\n\n')
    for i in range(len(netdevs)):
        if "network.type" in netdevs[i]:
            netdevs[i]=netdevs[i].replace('lxc.network','lxc.net.'+str(i))
        if "ipv4" in netdevs[i]:
            netdevs[i]=netdevs[i].replace('ipv4',"ipv4.address")
    return text.split('# Network configuration')[0]+'# Network configuration'+'\n\n'.join(netdevs)

def update_configs(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()
    # create a backup of the original file
    os.rename(file_path, file_path + '.bak')
    if "lxc.net" in contents:
        contents=update_network_configs(contents)
    if "rootfs.backend" in contents:
        contents=contents.replace('lxc.rootfs = ','lxc.rootfs.path = dir:')
        contents=contents.replace('\nlxc.rootfs.backend','\n# lxc.rootfs.backend')
    if "lxc.utsname" in contents:
        contents=contents.replace('lxc.utsname','lxc.uts.name')
    with open(file_path, 'w') as file:
        file.write(contents)
def update_all_configs(directory):
    for root, dirs, files in tqdm(os.walk(directory)):
        for file in files:
            if "config" in file and "bak" not in file:
                update_configs(os.path.join(root, file))

def main():
    # check if the user has provided a directory or a file
    if len(sys.argv) != 2:
        print('Usage: update_configs.py <directory or file>')
        sys.exit(1)
    path = sys.argv[1]
    print('Updating the configuration files in', path, '.')
    print('This may take a while...')
    if os.path.isdir(path):
        update_all_configs(path)
    elif os.path.isfile(path):
        update_configs(path)
    else:
        print('The specified file or directory does not exist')
        sys.exit(1)

if __name__ == '__main__':
    main()