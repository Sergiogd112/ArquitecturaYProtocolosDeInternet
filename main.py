import numpy as np
from pprint import pprint
from net import Net

def main():
    routers = {
        "R01": {"eth0": ["br01"], "eth1": ["br02"], "eth2": ["br03"]},
        "R02": {"eth0": ["br03"], "eth1": ["br05"], "eth2": ["br04"]},
        "R03": {
            "eth0": ["br05"],
            "eth1": ["br08", "10.0.0.97/28"],
            "eth2": ["br06", "10.0.0.113/29"],
        },
        "R04": {
            "eth0": ["br08", "10.0.0.98/28"],
            "eth1": ["br09", "10.0.0.1/26"],
            "eth2": ["br07", "10.0.0.65/27"],
        },
        "R05": {
            "eth0": ["br0"],
            "eth1": ["br06", "10.0.0.114/29"],
            "eth2": ["br10", "10.0.0.121/29"],
        },
    }
    net=Net(
        {
            "R01": {"eth0": ["br01"], "eth1": ["br02"], "eth2": ["br03"]},
            "R02": {"eth0": ["br03"], "eth1": ["br05"], "eth2": ["br04"]},
            "R03": {
                "eth0": ["br05"],
                "eth1": ["br08", "10.0.0.97/28"],
                "eth2": ["br06", "10.0.0.113/29"],
            },
            "R04": {
                "eth0": ["br08", "10.0.0.98/28"],
                "eth1": ["br09", "10.0.0.1/26"],
                "eth2": ["br07", "10.0.0.65/27"],
            },
            "R05": {
                "eth0": ["br04"],
                "eth1": ["br06", "10.0.0.114/29"],
                "eth2": ["br10", "10.0.0.121/29"],
            },
        }
    )
    net.netdict["br01"]["devcount"] = 2 + 60
    net.netdict["br02"]["devcount"] = 2 + 20
    net.netdict["br03"]["devcount"] = 2 + 12
    net.netdict["br04"]["devcount"] = 2 + 6
    net.netdict["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/24")
    expected={
        "br01": {
            "routers": ["R01"],
            "devcount": 62,
            "netip": "10.0.0.128",
            "mask": 26,
            "maxdevices": 64,
        },
        "br02": {
            "routers": ["R01"],
            "devcount": 22,
            "netip": "10.0.0.192",
            "mask": 27,
            "maxdevices": 32,
        },
        "br03": {
            "routers": ["R01", "R02"],
            "devcount": 14,
            "netip": "10.0.0.224",
            "mask": 28,
            "maxdevices": 16,
        },
        "br05": {
            "routers": ["R02", "R03"],
            "devcount": 8,
            "netip": "10.0.0.248",
            "mask": 29,
            "maxdevices": 8,
        },
        "br04": {
            "routers": ["R02","R05"],
            "devcount": 8,
            "netip": "10.0.0.240",
            "mask": 29,
            "maxdevices": 8,
        },
        "br08": {
            "routers": ["R03", "R04"],
            "devcount": 4,
            "netip": "10.0.0.96",
            "mask": 28,
            "maxdevices": 16,
        },
        "br06": {
            "routers": ["R03", "R05"],
            "devcount": 4,
            "netip": "10.0.0.112",
            "mask": 29,
            "maxdevices": 8,
        },
        "br09": {
            "routers": ["R04"],
            "devcount": 3,
            "netip": "10.0.0.0",
            "mask": 26,
            "maxdevices": 64,
        },
        "br07": {
            "routers": ["R04"],
            "devcount": 3,
            "netip": "10.0.0.64",
            "mask": 27,
            "maxdevices": 32,
        },
        "br10": {
            "routers": ["R05"],
            "devcount": 3,
            "netip": "10.0.0.120",
            "mask": 29,
            "maxdevices": 8,
        },
    }
    for key, value in net.netdict.items():
        print(key)
        pprint(value)
        pprint(expected[key])
        assert value == expected[key] 


if __name__ == "__main__":
    main()
