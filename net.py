from ip import *
from binmanipulation import getFirstSetBitPos
import numpy as np


class Net:
    def __init__(self, routers, netdict=None):
        self.netdict = netdict
        if netdict is None:
            self.netdict = Net.generate_netdict(routers)
        self.routers = routers
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
        print(netdict)
        return netdict

    def fix_ranges(ranges):
        res = []
        for ran in ranges:
            print(ranges)
            # (32,127,None)
            if ran[2] is None:
                maskstart = 33 - getFirstSetBitPos(ran[0])  # 27
                maskend = 33 - getFirstSetBitPos(~ran[1])  # 25
                netipintend = ip_to_int(get_net_ip(int_to_ip(ran[1]), maskend))  # 0
                broadipintstart = ip_to_int(
                    get_broadcast(int_to_ip(ran[0]), maskstart)
                )  # 63
                print(maskstart, maskend, netipintend, broadipintstart)
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
        print(rstart, rend)
        print(used_ranges)
        available = []
        if rstart != used_ranges[0][0]:
            available += [(rstart, used_ranges[0][0] - 1, None)]
        if rend != used_ranges[0][1]:
            available += [(used_ranges[0][1] + 1, rend, None)]

        for i, ran in enumerate(used_ranges[:-1]):
            if ran[1] + 1 != used_ranges[i + 1][0]:
                available += [(ran[1] + 1, used_ranges[i][0] - 1, None)]
        self.emptyranges = Net.fix_ranges(available)
        return self.emptyranges

    def assign_subrange(self, mainnetip, mask=None, compact=True):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        self.get_usable_ranges(mainnetip, mask)
        brgs = list(self.netdict.keys())
        sorted(brgs, key=lambda x: self.netdict[x]["devcount"], reverse=True)
        for brg in brgs:
            if "netip" in self.netdict[brg].keys():
                continue
            mask = 32-np.ceil(np.log2(self.netdict[brg]["devcount"]))
            
