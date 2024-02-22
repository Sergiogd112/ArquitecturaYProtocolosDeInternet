lxcpath="/var/lib/lxc"
backuppath=$1
# iterate through all containers
for container in $(ls $lxcpath); do
    # check if the container is running
    if [ $(lxc-info -n $container | grep "RUNNING" | wc -l) -eq 1 ]; then
        # stop the container
        lxc-stop -n $container
    fi
    cd $lxcpath
    # create a backup of the container
   tar --numeric-owner -czvf $backuppath/$container.tar.gz $container
done