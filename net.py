import os
from typing import Tuple, Union
from pprint import pprint

from tqdm import tqdm
import numpy as np
from colorama import Fore, Style
from matplotlib import pyplot as plt
import networkx as nx

from rich.console import Console
from route import RouteTable
from ip import ip_to_int, int_to_ip, get_net_ip, get_broadcast, ping
from binmanipulation import getFirstSetBitPos


class Net:

    def __init__(
        self,
        routers: dict,
        netdict: Union[dict, None] = None,
        routes: Union[dict, None] = None,
    ):
        """
        Initializes a Net object.

        Parameters:
        - routers (list): A list of routers in the network.
        - netdict (dict, optional): A dictionary representing the network topology.
            If not provided, it will be generated based on the routers.
        - routes (dict, optional): A dictionary representing the routing table.
            If not provided, it will be empty.

        Returns:
        None
        """
        self.netdict = netdict
        self.routers = routers
        if netdict is None:
            self.netdict = self.generate_netdict(routers)
        if routes is None:
            self.routes = {}
            # self.generate_routes(routers)
        self.emptyranges = []

    def generate_netdict(self, routers: dict) -> dict:
        """
        Generate a network dictionary based on the given routers.

        Args:
            routers (dict): A dictionary containing router information.

        Returns:
            dict: A network dictionary with bridge, router, and network information.
        """
        netdict = {}
        for router, value in routers.items():
            Console().print(router)
            Console().print(value)
            for _, con in value["iface"].items():
                brg = con["brg"]
                if brg is None:
                    continue
                if brg not in netdict:
                    netdict[brg] = {"routers": [router], "devcount": 3}
                else:
                    netdict[brg]["routers"].append(router)
                    netdict[brg]["routers"] = sorted(netdict[brg]["routers"])
                    netdict[brg]["devcount"] += 1
                if len(con) > 1:
                    netdict[brg]["netip"] = get_net_ip(con["ip"])
                    netdict[brg]["mask"] = int(con["ip"].split("/")[1])
                    netdict[brg]["maxdevices"] = 2 ** (32 - netdict[brg]["mask"])
        return netdict

    @staticmethod
    def read_scenario(escenario: str) -> "Net":
        routers = {}
        path = "/home/api/practiques/" + escenario.split("-")[0] + "/" + escenario
        # if this path is not a directory set it to:
        if not os.path.isdir(path):
            path = os.path.join("practiques", escenario.split("-")[0], escenario)
        for el in os.listdir(path):
            if (
                "config" in el
                and "bak" not in el
                and os.path.isdir(os.path.join(path, el))
            ):
                break
        else:
            raise FileNotFoundError("No config directory found")
        for config in os.listdir(os.path.join(path, el)):
            if "config" in config and "bak" not in config:
                with open(
                    os.path.join(path, el, config), "r", encoding="utf-8"
                ) as file:
                    contents = file.read()
                name, conf = Net.lxc_to_router(contents)
                routers[name] = conf
        return Net(routers)

    @staticmethod
    def lxc_to_router(text: str) -> Tuple[str, dict]:
        # Your code here
        text = text.strip()
        # get the uts.name
        utsname = text.split("lxc.uts.name = ")[1].split("\n")[0]
        # get the network configuration
        netconf = text.split("# Network configuration")[1].split("\n\n")
        netcondict = {"iface": {}}
        # console = Console()
        # console.print("\n\n".join(netconf))
        for block in netconf:
            if len(block) == 0:
                continue
            # get the name of the interface

            name = block.split(".name = ")[1].split("\n")[0].strip()
            try:
                brg = block.split(".link = ")[1].split("\n")[0].strip()
            except IndexError:
                brg = None
            if "address" in block:
                # get the ip address
                address = block.split("address = ")[1].split("\n")[0].strip()
                netcondict["iface"][name] = {
                    "brg": brg,
                    "ip": address,
                }
            else:
                netcondict["iface"][name] = {"brg": brg}

        return (utsname, netcondict)

    def read_vtyshrc(self, contents: str) -> Tuple[int, dict]:
        """example contents:
                !
        interface eth0
          ip address 10.0.1.193/27
        !
        interface eth1
          ip address 10.0.1.97/27
        !
        !
        !
        ip forwarding
        ipv6 forwarding
        returns:
                {
                    "eth0": {"brg":None,"ip":"10.0.1.193/27"},
                    "eth1": {"brg":None,"ip":"10.0.1.97/27"},
                }
        """
        blocks = contents.split("!\n")[1:]
        res = {"iface": {}}
        changes = 0
        for block in blocks:
            if "interface" in block:
                name = block.split("interface ")[1].split("\n")[0]
                res["iface"][name] = {}
                if "ip address" in block:
                    address = block.split("ip address ")[1].split("\n")[0]
                    res["iface"][name] = {"brg": None, "ip": address}
                    changes += 1
                if "ip ospf" in block:
                    res["iface"][name]["ospf"] = block.split("ip ospf ")[1].split("\n")[
                        0
                    ]
                    changes += 1
                else:
                    res[name] = {"brg": None}
                    changes += 1
            if "router ospf" in block:
                if "ospf" not in res:
                    res["ospf"] = []
                for line in block.split("\n")[1:]:
                    Console().print(line)
                    if "network" not in line:
                        continue
                    area = line.split("area ")[1].split("\n")[0]
                    net = line.split("network ")[1].split(" ")[0]
                    if area not in res["ospf"].keys():
                        res["ospf"] += [{"area": area, "network": net}]
                        changes += 1
        Console().print(res)
        return changes, res

    def read_scenario_subconfigs(self, escenario: str, sub: str) -> "Net":
        path = "/home/api/practiques/" + escenario.split("-")[0] + "/" + escenario
        # if this path is not a directory set it to:
        if not os.path.isdir(path):
            path = os.path.join("practiques", escenario.split("-")[0], escenario)
        for el in os.listdir(path):
            if (
                "config" in el
                and "bak" not in el
                and os.path.isdir(os.path.join(path, el))
            ):
                break
        else:
            raise FileNotFoundError("No config directory found")
        for file in os.listdir(os.path.join(path, el)):
            if sub in file:
                router = file.split("_")[1]
                Console().print(router)
                with open(os.path.join(path, el, file), "r", encoding="utf-8") as file:
                    contents = file.read()
                ch, res = self.read_vtyshrc(contents)
                if ch < 1:
                    continue
                for port, conf in res["iface"].items():
                    Console().print(port)
                    Console().print(conf)
                    if len(conf) < 1:
                        continue

                    if router not in self.routers.keys():
                        self.routers[router] = {"iface": {port: {"brg": conf["brg"]}}}
                    if "ospf" in res:
                        self.routers[router]["iface"][port]["ospf"] = res["ospf"]
                        continue
                    if port not in self.routers[router].keys():
                        self.routers[router]["iface"][port] = {"brg": conf["brg"]}
                    if len(conf) <= 1:
                        self.routers[router]["iface"][port]["brg"] = self.routers[
                            router
                        ][port]["brg"]
                    else:
                        self.routers[router]["iface"][port] = {
                            "brg": self.routers[router]["iface"][port]["brg"],
                            "ip": (
                                conf["ip"]
                                if conf["ip"] is not None
                                else (
                                    self.routers[router]["iface"][port]["ip"]
                                    if "ip" in self.routers[router]["iface"][port]
                                    else None
                                )
                            ),
                        }
                if "ospf" in res:
                    self.routers[router]["ospf"] = res["ospf"]
        self.netdict = self.generate_netdict(self.routers)

    def generate_routes(self, routers=None):
        if routers is None:
            routers = self.routers
        for router, value in routers.items():
            if router not in self.routes:
                self.routes[router] = RouteTable()
            for port, con in value["iface"].items():
                if len(con) > 1:
                    if con["brg"] in self.netdict.keys():

                        self.routes[router].add_route(
                            {
                                "Type": "C",
                                "Destination": self.netdict[con["brg"]]["netip"],
                                "Cost": "0",
                                "NextHop": "direct connect",
                                "Interface": port,
                                "Mask": int(con["ip"].split("/")[1]),
                                "Selected": True,
                                "MyCost": 0,
                                "Configured": True,
                            }
                        )

        return self.routes

    @staticmethod
    def fix_ranges(ranges: list) -> list:
        res = []
        for ran in ranges:
            # (32,127,None)
            if ran[2] is None:
                # print(ran)
                maskstart = 33 - getFirstSetBitPos(ran[0])  # 27
                maskend = 33 - getFirstSetBitPos(~ran[1])  # 25
                netipintend = ip_to_int(get_net_ip(int_to_ip(ran[1]), maskend))  # 0
                broadipintstart = ip_to_int(
                    get_broadcast(int_to_ip(ran[0]), maskstart)
                )  # 63
                # print(maskstart, maskend, netipintend, broadipintstart)
                if maskstart == maskend:
                    if netipintend == ran[0]:
                        res += [(ran[0], ran[1], maskstart)]
                    elif netipintend == 1 + broadipintstart:
                        res += [
                            (ran[0], broadipintstart, maskstart),
                            (netipintend, ran[1], maskend),
                        ]
                    else:
                        res += (
                            [(ran[0], broadipintstart, maskstart)]
                            + Net.fix_ranges(
                                [(broadipintstart + 1, netipintend - 1, None)]
                            )
                            + [(netipintend, ran[1], maskend)]
                        )
                elif maskstart > maskend:
                    if broadipintstart == ran[1]:
                        res += [(ran[0], ran[1], maskstart)]
                    elif netipintend == 1 + broadipintstart:
                        res += [
                            (ran[0], broadipintstart, maskstart),
                            (netipintend, ran[1], maskend),
                        ]

                    else:
                        res += [(ran[0], broadipintstart, maskstart)] + Net.fix_ranges(
                            [(broadipintstart + 1, ran[1], None)]
                        )

                elif maskstart < maskend:
                    if netipintend == ran[0]:
                        res += [(ran[0], ran[1], maskend)]
                    elif netipintend == 1 + broadipintstart:
                        res += [
                            (ran[0], broadipintstart, maskstart),
                            (netipintend, ran[1], maskend),
                        ]
                    else:
                        res += Net.fix_ranges([(ran[0], netipintend - 1, None)]) + [
                            (netipintend, ran[1], maskend)
                        ]
                else:
                    raise ValueError("Either you found a bug in the code or broke math")

        return res

    def get_usable_ranges(self, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        ranges = []
        for _, conf in self.netdict.items():
            if "netip" in conf.keys():
                ranges = ranges + [
                    (
                        ip_to_int(conf["netip"]),
                        ip_to_int(get_broadcast(conf["netip"], conf["mask"])),
                        conf["mask"],
                    )
                ]
        used_ranges = sorted(ranges, key=lambda x: x[0])
        rstart = ip_to_int(get_net_ip(mainnetip, mask))

        rend = ip_to_int(get_broadcast(mainnetip, mask))
        # print(rstart, rend)
        # print(used_ranges)
        available = []
        if rstart != used_ranges[0][0]:
            available += [(rstart, used_ranges[0][0] - 1, None)]
        if rend != used_ranges[0][1]:
            available += [(used_ranges[0][1] + 1, rend, None)]

        for i, ran in enumerate(used_ranges[:-1]):
            if ran[1] + 1 != used_ranges[i + 1][0]:
                available += [(ran[1] + 1, used_ranges[i][0] - 1, None)]
        self.emptyranges = Net.fix_ranges(available)
        self.emptyranges = sorted(self.emptyranges, key=lambda x: x[0])

        return self.emptyranges

    @staticmethod
    def print_ranges_with_ip(ranges: list):
        for ran in ranges:
            print(int_to_ip(ran[0]), int_to_ip(ran[1]), ran[2])

    def assign_subnets(self, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        self.get_usable_ranges(mainnetip, mask)
        brgs = list(self.netdict.keys())
        brgs = sorted(
            brgs, key=lambda x: (self.netdict[x]["devcount"], x), reverse=True
        )

        tempranges = []
        for brg in brgs:
            if "netip" in self.netdict[brg].keys():
                continue
            ranges = sorted(
                self.emptyranges,
                key=lambda x: x[2],
            )
            # print(brg)
            # pprint(self.netdict[brg])
            # Net.print_ranges_with_ip(ranges)
            mask = 32 - int(np.ceil(np.log2(self.netdict[brg]["devcount"])))
            tempranges = ranges.copy()

            # print(mask)

            for n, ran in enumerate(ranges):
                # print(int_to_ip(ran[0]), int_to_ip(ran[1]), ran[2])
                if ran[2] == mask:
                    self.netdict[brg]["netip"] = int_to_ip(ran[0])
                    self.netdict[brg]["mask"] = mask
                    self.netdict[brg]["maxdevices"] = 2 ** (32 - mask)
                    tempranges.pop(n)
                    break
                elif ran[2] < mask:
                    self.netdict[brg]["netip"] = int_to_ip(ran[0])
                    self.netdict[brg]["mask"] = mask
                    self.netdict[brg]["maxdevices"] = 2 ** (32 - mask)
                    tempranges.pop(n)
                    tempranges += [
                        (
                            ip_to_int(get_broadcast(int_to_ip(ran[0]), mask)) + 1,
                            ran[1],
                            None,
                        )
                    ]
                    self.emptyranges = Net.fix_ranges(tempranges)

                    # print("===" * 10)
                    # Net.print_ranges_with_ip(ranges)
                    # print("===" * 10)
                    # Net.print_ranges_with_ip(
                    #     [
                    #         (
                    #             ip_to_int(get_broadcast(int_to_ip(ran[0]), mask)) + 1,
                    #             ran[1],
                    #             None,
                    #         )
                    #     ]
                    # )
                    # print("===" * 10)

                    ranges = sorted(ranges, key=lambda x: x[2])
                    # Net.print_ranges_with_ip(ranges)
                    # pprint(self.netdict[brg])
                    break
            else:
                raise RuntimeError("No more ranges available")
            # print("===" * 10)
            # print("===" * 10)
        return self.netdict

    def get_router_port_from_brdg(self, router, brg):
        for port, con in self.routers[router]["iface"].items():
            if con["brg"] == brg:
                return port
        return None

    def check_ip_used(self, ip, brg):
        for router in self.netdict[brg]["routers"]:
            for _, con in self.routers[router]["iface"].items():
                if len(con) == 1:
                    continue
                if con["brg"] != brg:
                    continue
                if ip in con["ip"]:
                    return True
        return False

    def assign_ips(self, apply=False):
        commands = []
        for router, value in self.routers.items():
            for port, con in value["iface"].items():
                if len(con) > 1:
                    continue
                brg = con["brg"]
                portip = (
                    int_to_ip(
                        ip_to_int(self.netdict[brg]["netip"])
                        + self.netdict[brg]["routers"].index(router)
                        + 1
                    )
                    + "/"
                    + str(self.netdict[brg]["mask"])
                )
                for i in range(
                    ip_to_int(portip.split("/", maxsplit=1)[0]),
                    ip_to_int(get_broadcast(portip)) - 1,
                ):
                    if not self.check_ip_used(int_to_ip(i), brg):
                        portip = int_to_ip(i) + "/" + str(self.netdict[brg]["mask"])
                        break
                self.routers[router]["iface"][port]["ip"] = portip
                if apply:
                    commands.append(
                        f"lxc-attach -n {router} -- ip addr add {portip} dev {port}"
                    )
        return self.routers, commands

    def generate_non_direct_routes(self, unconfigured=None):
        if unconfigured is None:
            unconfigured = list(self.routers.keys())
        i = 0
        while len(unconfigured) > 0:
            # print("===" * 20)
            # print("===" * 20)
            if i > 1000:
                raise RuntimeError("Infinite loop")
            router = unconfigured.pop(0)
            # print(router)
            con = self.routers[router]
            # print(self.routes[router].format_table())
            for _, conf in con["iface"].items():
                if len(conf) == 1:
                    continue
                brg = conf[0]
                # print("===" * 20)

                # print(f"Checking {brg} {self.netdict[brg]['netip']} {conf[1]} {port}")
                for nextrouter in self.netdict[brg]["routers"]:

                    if nextrouter == router:
                        continue
                    neightport = self.get_router_port_from_brdg(nextrouter, brg)
                    if neightport is None:
                        continue
                    updates = 0
                    # print(f"Checking {nextrouter} {neightport}")
                    for _, route in self.routes[router].table.iterrows():
                        if route["Destination"] != self.netdict[brg]["netip"]:
                            updates += int(
                                self.routes[nextrouter].add_route(
                                    {
                                        "Type": "S",
                                        "Destination": (route["Destination"]),
                                        "Cost": 0,
                                        "NextHop": conf["ip"],
                                        "Interface": neightport,
                                        "Mask": route["Mask"],
                                        "Selected": True,
                                        "MyCost": route["MyCost"] + 1,
                                        "Configured": False,
                                    }
                                )
                            )
                    if updates > 0:
                        unconfigured.append(nextrouter)
        for router, routes in self.routes.items():
            # print(router)
            # print(routes.format_table())
            routes.merge_static_by_supernet()

    def generate_static_commands(self):
        commands = []
        for router, routes in self.routes.items():
            # print(router)
            # print(routes.format_table())
            commands += routes.generate_static_routing_commands(router)
        return commands

    def check_all_connections(self, visually=False):
        res = np.zeros((len(self.routers.keys()), len(self.routers.keys())))
        if visually:
            iterator = tqdm(enumerate(sorted(self.routers.keys())))
        else:
            iterator = enumerate(self.routers.items())
        for i, startrouter in iterator:
            for j, (endrouter, endvalue) in enumerate(self.routers.items()):
                # if startrouter == endrouter:
                #     continue
                for _, econ in endvalue["iface"].items():
                    if len(econ) > 1:
                        check = self.check_connection(
                            startrouter, econ["ip"].split("/")[0]
                        )
                        if visually and not check:
                            # print ERROR in red and bold if the connection fails
                            print(
                                f"lxc-attach -n {startrouter} -- "
                                + f"ping -c 1 -W 1 { econ['ip'].split('/')[0]}"
                            )
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"ERROR: {startrouter} -> {endrouter} {econ['ip'].split('/')[0]}"
                                + Style.RESET_ALL
                            )
                        # elif visually:
                        #     print(
                        #         Fore.GREEN
                        #         + Style.BRIGHT
                        #         + f"OK: {startrouter} -> {endrouter} {econ[1].split('/')[0]}"
                        #         + Style.RESET_ALL
                        #     )
                        res[i, j] += int(check)
                res[i, j] = res[i, j] // (len(endvalue["iface"].keys()))
        pprint(res)
        return np.float64(np.sum(res)), np.float64(len(self.routers.keys()) ** 2)

    def check_connection(self, router1, ip2) -> bool:
        res = ping(ip2, count=1, lxc_container=router1)
        if res is None:
            return False
        return float(res["loss"].replace("%", "").strip()) == 0

    def apply_configuration(self):
        commands = self.generate_static_commands()
        for command in commands:
            os.system(command)

    def to_nxgraph(self):
        graph = nx.DiGraph()
        for router, con in self.routers.items():
            graph.add_node(router)
            for port, conf in con["iface"].items():
                if len(conf) == 1:
                    continue
                brg = conf["brg"]
                for nextrouter in self.netdict[brg]["routers"]:
                    if nextrouter == router:
                        continue
                    neightport = self.get_router_port_from_brdg(nextrouter, brg)
                    if neightport is None:
                        continue
                    graph.add_edge(router, nextrouter, port=port, neightport=neightport)
        return graph

    def draw_graph(self):
        graph = self.to_nxgraph()
        pos = nx.spring_layout(graph)
        nx.draw(
            graph,
            pos,
            with_labels=True,
            node_color="skyblue",
            edge_color="black",
            width=1,
            alpha=0.7,
        )
        edge_labels = nx.get_edge_attributes(graph, "port")
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
        plt.show()

    def check_routes(self):
        for router, routes in self.routes.items():
            print(router)
            routes.check_table()

    def netdic_to_list(self):
        res = []
        for brg, conf in self.netdict.items():
            res.append(
                [
                    brg,
                    conf["devcount"],
                    conf["routers"],
                ]
            )
        return res
