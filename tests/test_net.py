from net import Net
from pytest import fixture
from pprint import pprint


@fixture
def net():
    return Net(
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
    assert net.netdict == {
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
    net.netdict["br01"]["devcount"] = 2 + 60
    net.netdict["br02"]["devcount"] = 2 + 20
    net.netdict["br03"]["devcount"] = 2 + 12
    net.netdict["br04"]["devcount"] = 2 + 6
    net.netdict["br05"]["devcount"] = 2 + 6
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
    for key, value in net.netdict.items():
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
    net.assign_subnets("10.0.0.0/24")
    net.assign_ips()
    expected = {
        "R01": {
            "eth0": ["br01", "10.0.0.129/26"],
            "eth1": ["br02", "10.0.0.193/27"],
            "eth2": ["br03", "10.0.0.225/28"],
        },
        "R02": {
            "eth0": ["br03", "10.0.0.226/28"],
            "eth1": ["br05", "10.0.0.249/29"],
            "eth2": ["br04", "10.0.0.241/29"],
        },
        "R03": {
            "eth0": ["br05", "10.0.0.250/29"],
            "eth1": ["br08", "10.0.0.97/28"],
            "eth2": ["br06", "10.0.0.113/29"],
        },
        "R04": {
            "eth0": ["br08", "10.0.0.98/28"],
            "eth1": ["br09", "10.0.0.1/26"],
            "eth2": ["br07", "10.0.0.65/27"],
        },
        "R05": {
            "eth0": ["br04", "10.0.0.242/29"],
            "eth1": ["br06", "10.0.0.114/29"],
            "eth2": ["br10", "10.0.0.121/29"],
        },
    }
