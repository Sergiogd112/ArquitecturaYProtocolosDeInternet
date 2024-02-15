from ip import *
from binmanipulation import getFirstSetBitPos
import numpy as np
from pprint import pprint
from route import RouteTable


class Net:
    def __init__(self, routers, netdict=None, routes=None):
        self.netdict = netdict
        self.routers = routers
        if netdict is None:
            self.netdict = Net.generate_netdict(routers)
        if routes is None:
            self.routes = {}
            # self.generate_routes(routers)
        self.emptyranges = []

    def generate_netdict(routers):
        netdict = {}
        for router, value in routers.items():
            for port, con in value.items():
                brg = con[0]
                if not (brg in netdict.keys()):
                    netdict[brg] = {"routers": [router], "devcount": 3}
                else:
                    netdict[brg]["routers"].append(router)
                    netdict[brg]["devcount"] += 1
                if len(con) > 1:
                    netdict[brg]["netip"] = get_net_ip(con[1])
                    netdict[brg]["mask"] = int(con[1].split("/")[1])
                    netdict[brg]["maxdevices"] = 2 ** (32 - netdict[brg]["mask"])
        return netdict

    def generate_routes(self, routers=None):
        if routers is None:
            routers = self.routers
        for router, value in routers.items():
            if not (router in self.routes.keys()):
                self.routes[router] = RouteTable()
            for port, con in value.items():
                if len(con) > 1:
                    self.routes[router].add_route(
                        {
                            "Type": "C",
                            "Destination": self.netdict[con[0]]["netip"],
                            "Cost": "0",
                            "NextHop": "direct connect",
                            "Interface": port,
                            "Mask": int(con[1].split("/")[1]),
                            "Selected": True,
                            "MyCost": 0,
                            "Configured": True,
                        }
                    )

        return self.routes

    def fix_ranges(ranges):
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
                    raise (
                        Exception("Either you found a bug in the code or broke math")
                    )

        return res

    def get_usable_ranges(self, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        ranges = []
        for brg, conf in self.netdict.items():
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

    def print_ranges_with_ip(ranges):
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
                raise Exception("No more ranges available")
            # print("===" * 10)
            # print("===" * 10)
        return self.netdict

    def get_router_port_from_brdg(self, router, brg):
        for port, con in self.routers[router].items():
            if con[0] == brg:
                return port
        return None

    def check_ip_used(self, ip, brg):
        for router in self.netdict[brg]["routers"]:
            for port, con in self.routers[router].items():
                if len(con) == 1:
                    continue
                if con[0] != brg:
                    continue
                if ip in con[1]:
                    return True
        return False

    def assign_ips(self, apply=False):
        commands = []
        for router, value in self.routers.items():
            for port, con in value.items():
                if len(con) > 1:
                    continue
                brg = con[0]
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
                    ip_to_int(portip.split("/")[0]),
                    ip_to_int(get_broadcast(portip)) - 1,
                ):
                    if not self.check_ip_used(int_to_ip(i), brg):
                        portip = int_to_ip(i) + "/" + str(self.netdict[brg]["mask"])
                        break
                self.routers[router][port].append(portip)
                if apply:
                    commands.append(
                        f"lxc-attach -n {router} -- ip addr add {portip} dev {port} && ip link set {port} up"
                    )
        return self.routers, commands

    def generate_non_direct_routes(self, apply=False, unconfigured=None):
        commands = []
        if unconfigured is None:
            unconfigured = list(self.routers.keys())
        i = 0
        while len(unconfigured) > 0:
            # print("===" * 20)
            # print("===" * 20)
            if i > 1000:
                raise Exception("Infinite loop")
            router = unconfigured.pop(0)
            # print(router)
            con = self.routers[router]
            # print(self.routes[router].format_table())
            for port, conf in con.items():
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
                    for idx, route in self.routes[router].table.iterrows():
                        if route["Destination"] != self.netdict[brg]["netip"]:
                            updates += int(
                                self.routes[nextrouter].add_route(
                                    {
                                        "Type": "S",
                                        "Destination": (route["Destination"]),
                                        "Cost": 0,
                                        "NextHop": conf[1],
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
            commands+=(
                routes.generate_static_routing_commands(router))
        return commands
