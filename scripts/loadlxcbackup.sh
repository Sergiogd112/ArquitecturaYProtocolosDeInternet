lxcpath="/var/lib/lxc"

backuppath=$1
# iterate through all containers
for container in $(ls $backuppath); do
    echo "Restoring $container at $backuppath/$container.tar.gz"
    # get the container name from the backup file
    container=$(echo $container | cut -d'.' -f1)
    mkdir /var/lib/lxc/$container/
    cd /var/lib/lxc/$container/
    # extract the backup of the container contents to the container's directory
    tar --numeric-owner -xzvf $backuppath/$container.tar.gz -C /var/lib/lxc/$container/
done