from pytest import fixture
from pprint import pprint
import pandas as pd
from rich.console import Console, Group
from rich.panel import Panel
from Net.ip import ip_to_int
from Net.ip import ip_to_int
from Net import Net,loaders

# from mytty import get_tty_width


@fixture
def net():
    return Net(
        {
            "R01": {
                "iface": {
                    "eth0": {"brg": "br01"},
                    "eth1": {"brg": "br02"},
                    "eth2": {"brg": "br03"},
                }
            },
            "R02": {
                "iface": {
                    "eth0": {"brg": "br03"},
                    "eth1": {"brg": "br05"},
                    "eth2": {"brg": "br04"},
                }
            },
            "R03": {
                "iface": {
                    "eth0": {"brg": "br05"},
                    "eth1": {"brg": "br08", "ip": "10.0.0.97/28"},
                    "eth2": {"brg": "br06", "ip": "10.0.0.113/29"},
                }
            },
            "R04": {
                "iface": {
                    "eth0": {"brg": "br08", "ip": "10.0.0.98/28"},
                    "eth1": {"brg": "br09", "ip": "10.0.0.1/26"},
                    "eth2": {"brg": "br07", "ip": "10.0.0.65/27"},
                }
            },
            "R05": {
                "iface": {
                    "eth0": {"brg": "br04"},
                    "eth1": {"brg": "br06", "ip": "10.0.0.114/29"},
                    "eth2": {"brg": "br10", "ip": "10.0.0.121/29"},
                }
            },
        }
    )


def test_fix_ranges():
    ranges = [(32, 223, None)]
    assert Net.fix_ranges(ranges) == [
        (32, 63, 27),
        (64, 127, 26),
        (128, 191, 26),
        (192, 223, 27),
    ]


def test_dict():
    assert {"a": 1, "b": 2} == {"b": 2, "a": 1}


def test_generate_netdict(net):
    assert net.bridges == {
        "br01": {"routers": ["R01"], "devcount": 3},
        "br02": {"routers": ["R01"], "devcount": 3},
        "br03": {"routers": ["R01", "R02"], "devcount": 4},
        "br05": {"routers": ["R02", "R03"], "devcount": 4},
        "br04": {"routers": ["R02", "R05"], "devcount": 4},
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


def test_assign_subnets(net):
    net.bridges["br01"]["devcount"] = 2 + 60
    net.bridges["br02"]["devcount"] = 2 + 20
    net.bridges["br03"]["devcount"] = 2 + 12
    net.bridges["br04"]["devcount"] = 2 + 6
    net.bridges["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/24")
    expected = {
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
        "br04": {
            "routers": ["R02", "R05"],
            "devcount": 8,
            "netip": "10.0.0.248",
            "mask": 29,
            "maxdevices": 8,
        },
        "br05": {
            "routers": ["R02", "R03"],
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
    for key, value in net.bridges.items():
        print(key)
        pprint(value)
        pprint(expected[key])
        assert value == expected[key]


def test_get_router_port_brdg(net):
    pprint(net.routers)
    assert net.get_router_port_from_brdg("R01", "br01") == "eth0"
    assert net.get_router_port_from_brdg("R01", "br02") == "eth1"
    assert net.get_router_port_from_brdg("R01", "br03") == "eth2"
    assert net.get_router_port_from_brdg("R02", "br03") == "eth0"
    assert net.get_router_port_from_brdg("R02", "br05") == "eth1"
    assert net.get_router_port_from_brdg("R02", "br04") == "eth2"
    assert net.get_router_port_from_brdg("R03", "br05") == "eth0"
    assert net.get_router_port_from_brdg("R03", "br08") == "eth1"
    assert net.get_router_port_from_brdg("R03", "br06") == "eth2"
    assert net.get_router_port_from_brdg("R04", "br08") == "eth0"
    assert net.get_router_port_from_brdg("R04", "br09") == "eth1"
    assert net.get_router_port_from_brdg("R04", "br07") == "eth2"
    assert net.get_router_port_from_brdg("R05", "br04") == "eth0"
    assert net.get_router_port_from_brdg("R05", "br06") == "eth1"
    assert net.get_router_port_from_brdg("R05", "br10") == "eth2"


def test_check_ip_used1(net):
    assert net.check_ip_used("10.0.0.1/26", "br09") == True


def test_check_ip_used97(net):
    assert net.check_ip_used("10.0.0.97/28", "br08") == True


def test_check_ip_used113(net):
    assert net.check_ip_used("10.0.0.113", "br06") == True


def test_check_ip_used100(net):
    assert net.check_ip_used("10.0.0.100", "br06") == False


def test_assign_ips(net):
    net.bridges["br01"]["devcount"] = 2 + 60
    net.bridges["br02"]["devcount"] = 2 + 20
    net.bridges["br03"]["devcount"] = 2 + 12
    net.bridges["br04"]["devcount"] = 2 + 6
    net.bridges["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/24")
    net.assign_ips()
    expected = {
        "R01": {
            "iface": {
                "eth0": {"brg": "br01", "ip": "10.0.0.129/26"},
                "eth1": {"brg": "br02", "ip": "10.0.0.193/27"},
                "eth2": {"brg": "br03", "ip": "10.0.0.225/28"},
            }
        },
        "R02": {
            "iface": {
                "eth0": {"brg": "br03", "ip": "10.0.0.226/28"},
                "eth1": {"brg": "br05", "ip": "10.0.0.241/29"},
                "eth2": {"brg": "br04", "ip": "10.0.0.249/29"},
            }
        },
        "R03": {
            "iface": {
                "eth0": {"brg": "br05", "ip": "10.0.0.242/29"},
                "eth1": {"brg": "br08", "ip": "10.0.0.97/28"},
                "eth2": {"brg": "br06", "ip": "10.0.0.113/29"},
            }
        },
        "R04": {
            "iface": {
                "eth0": {"brg": "br08", "ip": "10.0.0.98/28"},
                "eth1": {"brg": "br09", "ip": "10.0.0.1/26"},
                "eth2": {"brg": "br07", "ip": "10.0.0.65/27"},
            }
        },
        "R05": {
            "iface": {
                "eth0": {"brg": "br04", "ip": "10.0.0.250/29"},
                "eth1": {"brg": "br06", "ip": "10.0.0.114/29"},
                "eth2": {"brg": "br10", "ip": "10.0.0.121/29"},
            }
        },
    }
    pprint(net.routers)
    pprint(expected)
    for router, con in net.routers.items():
        print("===" * 20)
        for port, ip in con.items():
            print(router, port, ip)
            print(expected[router][port])
            assert ip == expected[router][port]


def test_generate_routes(net):
    net.bridges["br01"]["devcount"] = 2 + 60
    net.bridges["br02"]["devcount"] = 2 + 20
    net.bridges["br03"]["devcount"] = 2 + 12
    net.bridges["br04"]["devcount"] = 2 + 6
    net.bridges["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/24")
    net.assign_ips()
    net.generate_routes()
    console = Console()
    expected = {
        "R01": pd.DataFrame(
            {
                "Type": ["C", "C", "C"],
                "Destination": ["10.0.0.128", "10.0.0.192", "10.0.0.224"],
                "Mask": [26, 27, 28],
                "Cost": ["0", "0", "0"],
                "NextHop": ["direct connect"] * 3,
                "Interface": ["eth0", "eth1", "eth2"],
                "Selected": [True, True, True],
                "MyCost": [0, 0, 0],
                "Configured": [True, True, True],
            }
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        ),
        "R02": pd.DataFrame(
            {
                "Type": ["C", "C", "C"],
                "Destination": ["10.0.0.224", "10.0.0.240", "10.0.0.248"],
                "Mask": [28, 29, 29],
                "Cost": ["0", "0", "0"],
                "NextHop": ["direct connect"] * 3,
                "Interface": ["eth0", "eth1", "eth2"],
                "Selected": [True, True, True],
                "MyCost": [0, 0, 0],
                "Configured": [True, True, True],
            }
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        ),
        "R03": pd.DataFrame(
            {
                "Type": ["C", "C", "C"],
                "Destination": [
                    "10.0.0.112",
                    "10.0.0.240",
                    "10.0.0.96",
                ],
                "Mask": [29, 29, 28],
                "Cost": ["0", "0", "0"],
                "NextHop": ["direct connect"] * 3,
                "Interface": ["eth2", "eth0", "eth1"],
                "Selected": [True, True, True],
                "MyCost": [0, 0, 0],
                "Configured": [True, True, True],
            }
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        ),
        "R04": pd.DataFrame(
            {
                "Type": ["C", "C", "C"],
                "Destination": ["10.0.0.0", "10.0.0.64", "10.0.0.96"],
                "Mask": [26, 27, 28],
                "Cost": ["0", "0", "0"],
                "NextHop": ["direct connect"] * 3,
                "Interface": ["eth1", "eth2", "eth0"],
                "Selected": [True, True, True],
                "MyCost": [0, 0, 0],
                "Configured": [True, True, True],
            }
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        ),
        "R05": pd.DataFrame(
            {
                "Type": ["C", "C", "C"],
                "Destination": ["10.0.0.112", "10.0.0.120", "10.0.0.248"],
                "Mask": [29, 29, 29],
                "Cost": ["0", "0", "0"],
                "NextHop": ["direct connect"] * 3,
                "Interface": ["eth1", "eth2", "eth0"],
                "Selected": [True, True, True],
                "MyCost": [0, 0, 0],
                "Configured": [True, True, True],
            }
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        ),
    }
    for router, routes in net.routes.items():
        print("===" * 20)
        print("===" * 20)

        print(router)
        console.print(routes.format_table())
        expected[router] = (
            expected[router]
            .assign(intip=expected[router]["Destination"].apply(ip_to_int))
            .sort_values(
                by=["intip", "Mask"], ascending=[True, False], ignore_index=True
            )
            .drop(columns=["intip"])
        )
        print(expected[router])

        for col in routes.table.columns:
            print("===" * 20)
            print(routes.table[col])
            print(expected[router][col])
            for idx in routes.table.index:
                assert routes.table[col][idx] == expected[router][col][idx]
        pd.testing.assert_frame_equal(routes.table, expected[router])


def test_lxc_to_router_R01():

    content = """# Template used to create this container: /usr/share/lxc/templates/lxc-download
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
    """
    router, conf = loaders.lxc_to_router(content)
    assert router == "R01"
    assert conf == {
        "iface": {
            "eth0": {"brg": "br01"},
            "eth1": {"brg": "br02"},
            "eth2": {"brg": "br03"},
        }
    }


def test_lxc_to_router_R03():

    content = """# Template used to create this container: /usr/share/lxc/templates/lxc-download
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
lxc.rootfs.path = dir:/var/lib/lxc/R03/rootfs
# lxc.rootfs.backend = dir
lxc.uts.name = R03
# Network configuration
lxc.net.0.type = veth
lxc.net.0.link = br05
lxc.net.0.flags = up
lxc.net.0.name = eth0
lxc.net.0.ipv4.address = 10.0.0.250/29
lxc.net.0.veth.pair = R03-eth0 

lxc.net.1.type = veth
lxc.net.1.link = br08
lxc.net.1.flags = up
lxc.net.1.name = eth1
lxc.net.1.ipv4.address = 10.0.0.97/28
lxc.net.1.veth.pair = R03-eth1 

lxc.net.2.type = veth
lxc.net.2.link = br06
lxc.net.2.flags = up
lxc.net.2.name = eth2
lxc.net.2.ipv4.address = 10.0.0.113/29
lxc.net.2.veth.pair = R03-eth2
    """
    router, conf = loaders.lxc_to_router(content)
    assert router == "R03"
    assert conf == {
        "iface": {
            "eth0": {"brg": "br05", "ip": "10.0.0.250/29"},
            "eth1": {"brg": "br08", "ip": "10.0.0.97/28"},
            "eth2": {"brg": "br06", "ip": "10.0.0.113/29"},
        }
    }


def test_read_scenario(net):
    net2 = loaders.read_scenario("P01-E01")
    console = Console()
    console.print(Group(Panel(net.routers), Panel(net2.routers)))
    console.print(Group(Panel(net.bridges), Panel(net2.bridges)))
    for router, dev in net.routers.items():
        pprint(router)
        pprint(dev)
        pprint(net2.routers[router])
        for port, _ in dev.items():
            assert net.routers[router][port] == net2.routers[router][port]
    for brg, info in net.bridges.items():
        pprint(brg)
        pprint(info)
        pprint(net2.bridges[brg])
        assert net.bridges[brg] == net2.bridges[brg]

    assert net.routers == net2.routers
    assert net.bridges == net2.bridges


def test_get_brg_with_netip(net):
    brg = net.get_brg_with_netip("10.0.0.96")
    assert brg == "br08"
    brg = net.get_brg_with_netip("10.0.0.64")
    assert brg == "br07"
    brg = net.get_brg_with_netip("10.0.1.128")
    assert brg == None
