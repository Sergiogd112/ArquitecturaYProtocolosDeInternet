from ip import *
from binmanipulation import getFirstSetBitPos


class net:
    def __init__(self, routers, netdict=None):
        if netdict is None:
            self.netdict = net.generate_netdict(routers)
        self.netdict = netdict
        self.routers = routers
        self.ranges

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

    def fix_ranges(ranges):
        res = []
        for ran in ranges:
            # (32,127,None)
            if ran[2] is None:
                maskstart = 33 - getFirstSetBitPos(ran[0])  # 27
                maskend = 33 - getFirstSetBitPos(~ran[1])  # 25
                netipintend = ip_to_int(get_net_ip(int_to_ip(ran[1]), maskend))  # 0
                broadipintstart = ip_to_int(
                    get_broadcast(int_to_ip(ran[0]), maskstart)
                )  # 63

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
                            + fix_ranges([broadipintstart + 1, netipintend - 1, None])
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
                        res += [(ran[0], broadipintstart, maskstart)] + fix_ranges(
                            [broadipintstart + 1, ran[1], None]
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
                        res += fix_ranges([ran[0], netipintend - 1, None]) + [
                            (netipintend, ran[1], maskend)
                        ]
                else:
                    raise (
                        Exception("Either you found a bug in the code or broke math")
                    )

        return res

    def get_usable_ranges(netdict, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
        ranges = []
        for brg, conf in netdict.items():
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
        print(available)
        return available

    def assign_subrange(netdict, mainnetip, mask=None):
        if mask is None:
            mask = int(mainnetip.split("/")[1])
            mainnetip = mainnetip.split("/")[0]
