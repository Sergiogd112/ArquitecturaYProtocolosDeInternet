lxcpath="/var/lib/lxc"
backuppath=$1
# iterate through all containers
for container in $(ls $lxcpath); do
    mkdir /var/lib/lxc/$container/
    cd /var/lib/lxc/$NAME/
    tar --numeric-owner -xzvf container.tar.gz 
done