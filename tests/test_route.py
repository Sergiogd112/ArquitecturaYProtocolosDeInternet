from route import RouteTable
from pytest import fixture
from pandas import DataFrame
from pandas.testing import assert_frame_equal
import pandas as pd
from rich.console import Console
from rich.syntax import Syntax
import json
@fixture
def route():
    return RouteTable()


def test_add_route(route):
    route.add_route(
        {
            "Type": "C",
            "Destination": "10.0.0.0",
            "Cost": "0",
            "NextHop": "direct connect",
            "Interface": "eth0",
            "Mask": 24,
            "Selected": True,
            "MyCost": 0,
            "Configured": True,
        }
    )
    print(route.format_table())
    expected = DataFrame(
        {
            "Type": ["C"],
            "Destination": ["10.0.0.0"],
            "Mask": [24],
            "Cost": ["0"],
            "NextHop": ["direct connect"],
            "Interface": ["eth0"],
            "Selected": [True],
            "MyCost": [0],
            "Configured": [True],
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
    )
    print(expected)
    for col in route.table.columns:
        print(route.table[col][0], type(route.table[col][0]))
        print(expected[col][0], type(expected[col][0]))
        assert route.table[col][0] == expected[col][0]
    assert_frame_equal(route.table, expected)


def test_reset_routes(route):
    route.add_route(
        {
            "Type": "C",
            "Destination": "10.0.0.0",
            "Cost": "direct connect",
            "NextHop": "direct connect",
            "Interface": "eth0",
            "Mask": 24,
            "Selected": True,
            "MyCost": 0,
            "Configured": True,
        }
    )
    route.reset_routes()
    assert_frame_equal(
        route.table,
        DataFrame(
            columns=[
                "Type",
                "Destination",
                "Mask",
                "Cost",
                "NextHop",
                "Interface",
                "Selected",
                "MyCost",
                "Configured",
            ]
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
    )


def test_load_vtysh_routes(route):
    route.loads_vtysh_routes(
        """Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, N - NHRP,
       > - selected route, * - FIB route

O   10.1.1.0/24 [110/10] is directly connected, eth0, 03:15:24
C>* 10.1.1.0/24 is directly connected, eth0
O   10.1.2.0/24 [110/10] is directly connected, eth1, 03:14:44
C>* 10.1.2.0/24 is directly connected, eth1
O>* 10.1.3.0/24 [110/20] via 10.1.2.2, eth1, 03:14:43
O>* 10.1.4.0/24 [110/30] via 10.1.2.2, eth1, 03:14:33
O>* 10.1.5.0/24 [110/20] via 10.1.2.2, eth1, 03:14:43
O>* 10.1.6.0/24 [110/30] via 10.1.2.2, eth1, 03:14:39
O>* 10.1.7.0/24 [110/40] via 10.1.2.2, eth1, 03:14:38
O   10.1.8.0/24 [110/10] is directly connected, eth2, 03:14:44
C>* 10.1.8.0/24 is directly connected, eth2
O>* 10.1.9.0/24 [110/20] via 10.1.8.4, eth2, 03:14:39
O>* 10.1.10.0/24 [110/20] via 10.1.2.2, eth1, 03:14:43
O>* 10.1.11.0/24 [110/30] via 10.1.2.2, eth1, 03:14:33
  *                       via 10.1.8.4, eth2, 03:14:33
O>* 10.1.12.0/24 [110/30] via 10.1.2.2, eth1, 03:14:39
O>* 10.1.13.0/24 [110/20] via 10.1.8.4, eth2, 03:14:39
O>* 10.1.14.0/24 [110/20] via 10.1.8.4, eth2, 03:14:39
O>* 10.1.15.0/24 [110/30] via 10.1.8.4, eth2, 03:14:34
  *                       via 10.1.2.2, eth1, 03:14:34
O>* 10.1.16.0/24 [110/30] via 10.1.8.4, eth2, 03:14:34
O>* 10.1.17.0/24 [110/40] via 10.1.2.2, eth1, 03:14:38
C>* 127.0.0.0/8 is directly connected, lo
"""
    )
    console=Console()
    console.print(route.format_table())
    expected = pd.read_csv("tests/test.csv")
    for column in expected.columns:
        expected[column] = expected[column].astype(route.table[column].dtype)
    print(expected)
    assert route.table.equals(expected)
