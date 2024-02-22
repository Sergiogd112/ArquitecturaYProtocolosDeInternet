from ip import ip_to_int
from net import Net
from pytest import fixture
from pprint import pprint
import pandas as pd
from mytty import get_tty_width
from rich.console import Console


@fixture
def netospf():
    return Net.read_scenario("P03-E01")


def test_routers_org(netospf):
    assert netospf.routers == {
        "R04": {"iface": {"eth0": {"brg": "br06"}, "eth1": {"brg": "br03"}}},
        "R03": {"iface": {"eth0": {"brg": "br04"}, "eth1": {"brg": "br03"}}},
        "R02": {
            "iface": {
                "eth0": {"brg": "br01"},
                "eth1": {"brg": "br03"},
                "eth2": {"brg": "br05"},
            }
        },
        "R05": {
            "iface": {
                "eth0": {"brg": "br06"},
                "eth1": {"brg": "br05"},
                "eth2": {"brg": "br07"},
            }
        },
        "R06": {"iface": {"eth0": {"brg": "br08"}, "eth1": {"brg": None}}},
        "R01": {"iface": {"eth0": {"brg": "br02"}, "eth1": {"brg": "br03"}}},
    }


def test_netdict(netospf):
    net = netospf
    assert net.netdict is not None
    expected = {
        "br06": {"routers": ["R04", "R05"], "devcount": 4},
        "br03": {"routers": ["R01", "R02", "R03", "R04"], "devcount": 6},
        "br04": {"routers": ["R03"], "devcount": 3},
        "br01": {"routers": ["R02"], "devcount": 3},
        "br05": {"routers": ["R02", "R05"], "devcount": 4},
        "br07": {"routers": ["R05"], "devcount": 3},
        "br08": {"routers": ["R06"], "devcount": 3},
        "br02": {"routers": ["R01"], "devcount": 3},
    }
    assert net.netdict == expected


def test_load_zebra(netospf):
    net = netospf
    net.read_scenario_subconfigs("P03-E01", "zebra")
    expected = {
        "R04": {
            "iface": {
                "eth0": {"brg": "br06", "ip": "10.0.1.65/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.100/27"},
            }
        },
        "R03": {
            "iface": {
                "eth0": {"brg": "br04", "ip": "10.0.1.129/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.99/27"},
            }
        },
        "R02": {
            "iface": {
                "eth0": {"brg": "br01", "ip": "10.0.1.225/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.98/27"},
                "eth2": {"brg": "br05", "ip": "10.0.1.162/27"},
            }
        },
        "R05": {
            "iface": {
                "eth0": {"brg": "br06"},
                "eth1": {"brg": "br05"},
                "eth2": {"brg": "br07"},
            }
        },
        "R06": {"iface": {"eth0": {"brg": "br08"}, "eth1": {"brg": None}}},
        "R01": {
            "iface": {
                "eth0": {"brg": "br02", "ip": "10.0.1.193/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.97/27"},
            }
        },
    }
    assert net.routers == expected


def test_load_ospf(netospf):
    net = netospf
    net.read_scenario_subconfigs("P03-E01", "zebra")
    net.read_scenario_subconfigs("P03-E01", "ospf")

    expected = {
        "R04": {
            "iface": {
                "eth0": {"brg": "br06", "ip": "10.0.1.65/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.100/27"},
            },
            "ospf": [
                {"network": "10.0.1.64/27", "area": "0.0.0.1"},
                {"network": "10.0.1.96/27", "area": "0.0.0.1"},
            ],
        },
        "R03": {
            "iface": {
                "eth0": {"brg": "br04", "ip": "10.0.1.129/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.99/27"},
            },
            "ospf": [
                {"network": "10.0.1.128/27", "area": "0.0.0.1"},
                {"network": "10.0.1.96/27", "area": "0.0.0.1"},
            ],
        },
        "R02": {
            "iface": {
                "eth0": {"brg": "br01", "ip": "10.0.1.225/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.98/27"},
                "eth2": {"brg": "br05", "ip": "10.0.1.162/27"},
            },
            "ospf": [
                {"network": "10.0.1.96/27", "area": "0.0.0.1"},
                {"network" "10.0.1.160/27" "area" "0.0.0.1"},
                {"network": "10.0.1.224/27", "area": "0.0.0.1"},
            ],
        },
        "R05": {
            "iface": {
                "eth0": {"brg": "br06"},
                "eth1": {"brg": "br05"},
                "eth2": {"brg": "br07"},
            }
        },
        "R06": {"iface": {"eth0": {"brg": "br08"}, "eth1": {"brg": None}}},
        "R01": {
            "iface": {
                "eth0": {"brg": "br02", "ip": "10.0.1.193/27"},
                "eth1": {"brg": "br03", "ip": "10.0.1.97/27"},
            },
            "ospf": [
                {"network": "10.0.1.192/27", "area": "0.0.0.1"},
                {"network": "10.0.1.96/27", "area": "0.0.0.1"},
            ],
        },
    }
    assert net.routers == expected
