from net import Net
from pytest import fixture


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
                "eth0": ["br0"],
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
        "br04": {"routers": ["R02"], "devcount": 3},
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
        "br0": {"routers": ["R05"], "devcount": 3},
        "br10": {
            "routers": ["R05"],
            "devcount": 3,
            "netip": "10.0.0.120",
            "mask": 29,
            "maxdevices": 8,
        },
    }
