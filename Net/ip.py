import subprocess
from typing import Union


def ip_to_int(ip: str) -> int:
    return sum([int(byte) * 256 ** (3 - i) for i, byte in enumerate(ip.split("."))])


def int_to_ip(num: int) -> str:
    return ".".join([str((num // (256 ** (3 - i))) % 256) for i in range(4)])


def get_net_ip(ip: str, mask: int = None):
    if mask is None:
        mask = int(ip.split("/")[1])
        ip = ip.split("/")[0]
    devipint = ip_to_int(ip)
    maskint = int(256**4 - 2 ** (32 - int(mask)))
    netipint = int(devipint & maskint)
    return int_to_ip(netipint)


def get_broadcast(ip: str, mask: int = None) -> str:
    if mask is None:
        mask = int(ip.split("/")[1])
        ip = ip.split("/")[0]
    devipint = ip_to_int(ip)
    maskint = 256**4 - 2 ** (32 - int(mask))
    broadipint = int(devipint & maskint) + 2 ** (32 - int(mask)) - 1
    return int_to_ip(broadipint)


def ping(
    server: str = "example.com",
    count: int = 1,
    wait_sec: int = 1,
    lxc_container: str = None,
) -> Union[dict, None]:

    if lxc_container:
        cmd = "lxc-attach -n {} -- ping -c {} -W {} {}".format(
            lxc_container, count, wait_sec, server
        ).split(" ")
    else:
        cmd = "ping -c {} -W {} {}".format(count, wait_sec, server).split(" ")
    try:
        output = subprocess.check_output(cmd).decode().strip()
        lines = output.split("\n")
        total = lines[-2].split(",")[3].split()[1]
        loss = lines[-2].split(",")[2].split()[0]
        timing = lines[-1].split()[3].split("/")
        return {
            "type": "rtt",
            "min": timing[0],
            "avg": timing[1],
            "max": timing[2],
            "mdev": timing[3],
            "total": total,
            "loss": loss,
        }
    except Exception as e:
        return None
