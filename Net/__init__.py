import os
from typing import Tuple, Union
import numpy as np
from colorama import Fore, Style
from matplotlib import pyplot as plt
import networkx as nx
from subprocess import run

from rich.console import Console
from rich.prompt import Prompt
from rich.progress import track, Progress
from rich.panel import Panel

from .route import RouteTable
from Net.ip import ip_to_int, int_to_ip, get_net_ip, get_broadcast, ping
from binmanipulation import getFirstSetBitPos

# from .loaders import (
#     read_scenario,
#     lxc_to_router,
#     read_vtyshrc,
#     lxc_to_router_old,
#     lxc_to_router_new,
# )


class Net:
    def __init__(
        self,
        routers: dict,
        bridges: Union[dict, None] = None,
        routes: Union[dict, None] = None,
    ):
        """
        Initializes a Net object.

        Parameters:
        - routers (list): A list of routers in the network.
        - bridges (dict, optional): A dictionary representing the network topology.
            If not provided, it will be generated based on the routers.
        - routes (dict, optional): A dictionary representing the routing table.
            If not provided, it will be empty.

        Returns:
        None
        """
        self.bridges = bridges
        self.routers = routers

        if bridges is None:
            self.bridges = self.generate_bridges(routers)
        if routes is None:
            self.routes = {}
            # self.generate_routes(routers)
        self.emptyranges = []

    # Preprocessing
    def generate_bridges(self, routers: dict) -> dict:
        """
        Generate a network dictionary based on the given routers.

        Args:
            routers (dict): A dictionary containing router information.

        Returns:
            dict: A network dictionary with bridge, router, and network information.
        """
        bridges = {}
        for router, value in routers.items():
            # Console().print(router)
            # Console().print(value)
            for _, con in value["iface"].items():
                brg = con["brg"]
                if brg is None:
                    continue
                if brg not in bridges:
                    bridges[brg] = {"routers": [router], "devcount": 3}
                else:
                    bridges[brg]["routers"].append(router)
                    bridges[brg]["routers"] = sorted(list(set(bridges[brg]["routers"])))
                    bridges[brg]["devcount"] += 1
                if len(con) > 1 and con["ip"] is not None:
                    bridges[brg]["netip"] = get_net_ip(con["ip"])
                    bridges[brg]["mask"] = int(con["ip"].split("/")[1])
                    bridges[brg]["maxdevices"] = 2 ** (32 - bridges[brg]["mask"])
                if "ospf" in con:
                    bridges[brg]["ospf"] = con["ospf"]
        # Console().print(bridges)
        self.bridges = bridges
        for router, value in routers.items():
            # Console().print(router)
            if "ospf" in value:
                for ospf in value["ospf"]:
                    # Console().print(ospf)
                    # Console().print(self.get_brg_with_netip(ospf["network"].split("/")[0]))
                    bridge = bridges[
                        self.get_brg_with_netip(ospf["network"].split("/")[0])
                    ]
                    bridge["ospf"] = ospf

                    if "p2p" in value and value["p2p"]:
                        if len(bridge["routers"]) != 2:
                            Console().print(
                                "Error: p2p ospf network in bridge with more than 2 routers"
                            )
                            continue
                        if bridge["routers"][0] != router:
                            if (
                                self.routers[bridge["routers"][0]]["iface"][
                                    self.get_router_port_from_brdg(
                                        bridge["routers"][0], bridge
                                    )
                                ]["ospf"]
                                == "network point-to-point"
                            ):
                                bridge["routers"] = [router, bridge["routers"][0]]
                        continue
                    for crouter in bridge["routers"]:
                        if crouter not in routers.keys():
                            continue
                        if "ospf" not in routers[crouter]:
                            opt = Prompt.ask(
                                "Do you want to enable OSPF in " + crouter + "? (y/n)"
                            )
                            if opt == "y":
                                self.set_ospf(crouter, ospf["area"], ospf["network"])
                            else:
                                continue

        self.bridges = bridges
        return bridges

    # Getters
    def get_netips_from_router(self, router):
        """
        Retrieves a list of network IPs from the specified router.

        Args:
            router (str): The name of the router.

        Returns:
            list: A list of network IPs.

        """
        netips = []
        for _, conf in self.routers[router]["iface"].items():
            if len(conf) > 1 and "ip" in conf.keys() and conf["ip"] is not None:
                netips.append(get_net_ip(conf["ip"]))
        return netips

    def get_brg_with_netip(self, netip):
        """
        Returns the bridge associated with the given netip.

        Parameters:
        - netip (str): The netip to search for.

        Returns:
        - str or None: The bridge name if found, None otherwise.
        """
        # Console().print(netip)
        for brg, conf in self.bridges.items():
            # Console().print(conf)
            if "netip" not in conf.keys():
                continue
            if conf["netip"] == netip:
                return brg
        return None

    def generate_routes(self, routers=None):
        """
        Generates routes for the network based on the provided routers.

        Args:
            routers (dict): A dictionary containing the routers and their corresponding interfaces.

        Returns:
            dict: A dictionary representing the generated routes.
        """
        if routers is None:
            routers = self.routers
        for router, value in routers.items():
            if router not in self.routes:
                self.routes[router] = RouteTable()
            for port, con in value["iface"].items():
                if len(con) > 1:
                    if con["brg"] in self.bridges.keys():
                        self.routes[router].add_route(
                            {
                                "Type": "C",
                                "Destination": self.bridges[con["brg"]]["netip"],
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

    def get_router_port_from_brdg(self, router, brg):
        """
        Get the port of a router connected to a specific bridge.

        Args:
            router (str): The name of the router.
            brg (str): The name of the bridge.

        Returns:
            str or None: The port of the router connected to the bridge, or None if not found.
        """
        for port, con in self.routers[router]["iface"].items():
            if con["brg"] == brg:
                return port
        return None

    def get_ospf_areas(self) -> dict:
        """
        Get the OSPF areas for the network.

        Returns:
        dict: A dictionary containing the OSPF areas.
        """
        areas = {}
        for router, value in self.routers.items():
            if "ospf" in value:
                for ospf in value["ospf"]:
                    if ospf["area"] not in areas:
                        areas[ospf["area"]] = [router]
                    else:
                        areas[ospf["area"]] = list(set(areas[ospf["area"]] + [router]))
        Console().print(areas)
        return areas

    def bridges_to_list(self):
        res = []
        for brg, conf in self.bridges.items():
            res.append(
                [
                    brg,
                    conf["devcount"],
                    conf["routers"],
                ]
            )
        return res

    def get_router_with_ip(self, ip):
        for router, value in self.routers.items():
            for _, con in value["iface"].items():
                if con is None or "ip" not in con:
                    continue
                if con["ip"] is None:
                    continue
                if len(con) > 1 and ip in con["ip"]:
                    return router
        return None

    def get_asnums(self):
        asnums = []
        for _, con in self.routers:
            if "bgp" in con:
                asnums += [con["bgp"]["as"]]
        return asnums

    def get_router_ips(self, router) -> list:
        ips = []
        for _, con in self.routers[router]["iface"].items():
            if len(con) > 1 and "ip" in con:
                ips.append(con["ip"])
        return ips

    def get_net_from_bgp_as(self, asnum):
        for _, value in self.routers.items():
            if "bgp" in value and value["bgp"]["as"] == asnum:
                return value["bgp"]["network"]
        return None

    def get_neighbors(self, router):
        # gets the neighbors of a router that are in the same bridge
        neighbors = []
        for _, con in self.routers[router]["iface"].items():
            if len(con) > 1:
                brg = con["brg"]
                for nrouter in self.bridges[brg]["routers"]:
                    if nrouter == router:
                        continue
                    neighbors.append(nrouter)
        return neighbors

    def get_routers_with_bgp_as(self, asnum):
        routers = []
        for router, value in self.routers.items():
            if "bgp" in value and value["bgp"]["as"] == asnum:
                routers.append(router)
        return routers

    def __repr__(self):
        return f"Net({str(self.routers)}, {str(self.bridges)}, {str(self.routes)})"

    # Helpers
    def get_usable_ranges(self, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        ranges = []
        for _, conf in self.bridges.items():
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

    def check_ip_used(self, ip, brg):
        for router in self.bridges[brg]["routers"]:
            for _, con in self.routers[router]["iface"].items():
                if len(con) == 1:
                    continue
                if con["brg"] != brg:
                    continue
                if ip in con["ip"]:
                    return True
        return False

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

    @staticmethod
    def print_ranges_with_ip(ranges: list):
        for ran in ranges:
            print(int_to_ip(ran[0]), int_to_ip(ran[1]), ran[2])

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

                # print(f"Checking {brg} {self.bridges[brg]['netip']} {conf[1]} {port}")
                for nextrouter in self.bridges[brg]["routers"]:
                    if nextrouter == router:
                        continue
                    neightport = self.get_router_port_from_brdg(nextrouter, brg)
                    if neightport is None:
                        continue
                    updates = 0
                    # print(f"Checking {nextrouter} {neightport}")
                    for _, route in self.routes[router].table.iterrows():
                        if route["Destination"] != self.bridges[brg]["netip"]:
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
            iterator = track(list(enumerate(sorted(self.routers.keys()))))
        else:
            iterator = enumerate(self.routers.items())
        for i, startrouter in iterator:
            for j, endrouter in enumerate(sorted(list(self.routers.keys()))):
                endvalue = self.routers[endrouter]
                # if startrouter == endrouter:
                #     continue
                cons = 0
                for _, econ in endvalue["iface"].items():

                    if len(econ) > 1 and econ["ip"] is not None:
                        check = self.check_connection(
                            startrouter, econ["ip"].split("/")[0]
                        )
                        if visually and not check:
                            # print ERROR in red and bold if the connection fails
                            print(
                                f"lxc-attach -n {startrouter} -- "
                                + f"ping -c 1 -W 1 {econ['ip'].split('/')[0]}"
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
                        #         + f"OK: {startrouter} -> {endrouter} {econ['ip'].split('/')[0]}"
                        #         + Style.RESET_ALL
                        #     )
                        cons += 1
                        res[i, j] += int(check)
                if cons > 0:
                    res[i, j] = res[i, j] / np.float64(cons)
                else:
                    res[i, j] = 1
        Console().print(res)
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
                for nextrouter in self.bridges[brg]["routers"]:
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

    def tracepath(self, start, end):
        consoleout = run(
            ["/home/api/practiques/scripts/tracepath_api", start, end],
            capture_output=True,
            text=True,
        ).stdout
        return consoleout

    # Setters
    def assign_subnets(self, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        self.get_usable_ranges(mainnetip, mask)
        brgs = list(self.bridges.keys())
        brgs = sorted(
            brgs, key=lambda x: (self.bridges[x]["devcount"], x), reverse=True
        )

        tempranges = []
        for brg in brgs:
            if "netip" in self.bridges[brg].keys():
                continue
            ranges = sorted(
                self.emptyranges,
                key=lambda x: x[2],
            )
            # print(brg)
            # pprint(self.bridges[brg])
            # Net.print_ranges_with_ip(ranges)
            mask = 32 - int(np.ceil(np.log2(self.bridges[brg]["devcount"])))
            tempranges = ranges.copy()

            # print(mask)

            for n, ran in enumerate(ranges):
                # print(int_to_ip(ran[0]), int_to_ip(ran[1]), ran[2])
                if ran[2] == mask:
                    self.bridges[brg]["netip"] = int_to_ip(ran[0])
                    self.bridges[brg]["mask"] = mask
                    self.bridges[brg]["maxdevices"] = 2 ** (32 - mask)
                    tempranges.pop(n)
                    break
                elif ran[2] < mask:
                    self.bridges[brg]["netip"] = int_to_ip(ran[0])
                    self.bridges[brg]["mask"] = mask
                    self.bridges[brg]["maxdevices"] = 2 ** (32 - mask)
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
                    # pprint(self.bridges[brg])
                    break
            else:
                raise RuntimeError("No more ranges available")
            # print("===" * 10)
            # print("===" * 10)
        return self.bridges

    def assign_ips(self, apply=False):
        commands = []
        for router, value in self.routers.items():
            for port, con in value["iface"].items():
                if len(con) > 1:
                    continue
                brg = con["brg"]
                if "netip" not in self.bridges[brg].keys():
                    continue
                portip = (
                    int_to_ip(
                        ip_to_int(self.bridges[brg]["netip"])
                        + self.bridges[brg]["routers"].index(router)
                        + 1
                    )
                    + "/"
                    + str(self.bridges[brg]["mask"])
                )
                for i in range(
                    ip_to_int(portip.split("/", maxsplit=1)[0]),
                    ip_to_int(get_broadcast(portip)) - 1,
                ):
                    if not self.check_ip_used(int_to_ip(i), brg):
                        portip = int_to_ip(i) + "/" + str(self.bridges[brg]["mask"])
                        break
                self.routers[router]["iface"][port]["ip"] = portip
                if apply:
                    commands.append(
                        f"lxc-attach -n {router} -- vtysh -c 'configure terminal'"
                        + f" -c 'interface {port}' -c 'ip address {portip}'"
                    )
        return self.routers, commands

    def set_ip(self, router, iface, ip, apply=False):
        self.routers[router]["iface"][iface]["ip"] = ip
        if apply:
            os.system(
                f"lxc-attach -n {router} -- vtysh -c 'configure terminal' -c 'interface {iface}' -c 'ip address {ip}'"
            )
        self.bridges = self.generate_bridges(self.routers)

    def set_iface_ospf(self, router, iface, p2p, apply=False):
        Console().print(router, iface, p2p, apply)
        Console().print(
            self.routers[router]["iface"][iface]["brg"],
            self.bridges[self.routers[router]["iface"][iface]["brg"]]["routers"],
        )
        if (
            len(self.bridges[self.routers[router]["iface"][iface]["brg"]]["routers"])
            != 2
        ):
            Console().print(
                "Unable to set ospf on non point-to-point network, there are more than 2 routers connected to the bridge"
            )
            return
        self.routers[router]["iface"][iface]["ospf"] = (
            "point-to-point" if p2p == "y" else ""
        )
        if "ospf" not in self.routers[router].keys():
            Console().print("Adding ospf to router")
            area = Prompt.ask("Enter the area")
            netip = get_net_ip(self.routers[router]["iface"][iface]["ip"])
            self.routers[router]["ospf"] = [{"area": area, "network": netip}]
        if apply:
            if p2p == "y":
                os.system(
                    f"lxc-attach -n {router} -- vtysh -c 'configure terminal' -c 'interface {iface}'"
                    + " -c 'ip ospf network point-to-point'"
                )
            else:
                os.system(
                    f"lxc-attach -n {router} -- vtysh -c 'configure terminal' -c 'interface {iface}'"
                    + " -c 'no ip ospf network point-to-point'"
                )

    def set_ospf(self, router, area, netip, apply=False):
        if "ospf" not in self.routers[router].keys():
            self.routers[router]["ospf"] = []
        self.routers[router]["ospf"].append({"area": area, "network": netip})
        if apply:
            os.system(
                f"lxc-attach -n {router} -- vtysh -c 'configure terminal' "
                + f"-c 'router ospf' -c 'network {netip} area {area}'"
            )

    def set_bridge_netip(self, brg, netip, apply=False):
        self.bridges[brg]["netip"] = netip.split("/")[0]
        self.bridges[brg]["mask"] = int(netip.split("/")[1])
        if apply:
            _, commands = self.assign_ips(True)
            for command in commands:
                os.system(command)

    def set_bridge_connect(self, bridge, router, iface, plug=True, apply=False):
        if plug:
            self.routers[router]["iface"][iface]["brg"] = bridge
            if apply:
                os.system(f"brctl addif {bridge} {router}-{iface}")
        else:
            self.routers[router]["iface"][iface]["brg"] = None
            if apply:
                os.system(f"unplug-if-brg {bridge} {router}-{iface}")

        self.bridges = self.generate_bridges(self.routers)

    def set_bgp(self, router, asnum, router_id, network, apply=False):
        self.routers[router]["bgp"] = {"as": asnum, "id": router_id, "network": network}
        if apply:
            os.system(
                f"lxc-attach -n {router} -- vtysh -c 'configure terminal' -c 'router bgp {asnum}'"
                + f" -c 'bgp router-id {router_id}' -c 'network {network}'"
            )

    def next_hop(self, router, dest):
        consoleout = run(
            ["lxc-attach", "-n", router, "--", "ip", "route", "get", dest],
            capture_output=True,
            text=True,
        ).stdout
        via = consoleout.split("via ")[1].split(" ")[0].stip()
        dev = consoleout.split("dev ")[1].split(" ")[0].strip()
        src = consoleout.split("src ")[1].split(" ")[0].strip()
        uid = consoleout.split("uid ")[1].split(" ")[0].strip()
        return {"via": via, "dev": dev, "src": src, "uid": uid}

    def add_bgp_neighbor(self, router, neighbor_name, apply=False):
        if "bgp" not in self.routers[router].keys():
            Console().print("BGP not enabled in router")
            return
        if "neighbors" not in self.routers[router]["bgp"].keys():
            self.routers[router]["bgp"]["neighbors"] = []
        if "bgp" not in self.routers[neighbor_name].keys():
            Console().print("BGP not enabled in neighbor")
            return
        remote = self.routers[neighbor_name]["bgp"]["as"]
        nexthop = self.next_hop(
            neighbor_name, self.routers[router]["iface"]["eth0"]["ip"].split("/")[0]
        )
        neigh = self.routers[neighbor_name]["iface"][nexthop["dev"]]["ip"].split("/")[0]
        self.routers[router]["bgp"]["neighbors"].append(
            {
                "name": neighbor_name,
                "remote": remote,
                "nexthop": nexthop,
                "neigh": neigh,
            }
        )
        if apply:
            os.system(
                f"lxc-attach -n {router} -- vtysh -c 'configure terminal' -c 'router bgp {self.routers[router]['bgp']['as']}'"
                + f" -c 'neighbor {neigh} remote-as {remote}'"
            )
