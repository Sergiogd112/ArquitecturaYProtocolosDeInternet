from scapy.all import rdpcap
from scapy.layers.inet import IP, UDP, TCP
from scapy.contrib.bgp import *
from scapy.utils import PcapReader
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.pretty import Pretty
import os
from Net.ip import get_net_ip, ip_to_int
import pandas as pd


class BGP_table:
    def __init__(self):
        self.table = pd.DataFrame(
            columns=[
                "selected",
                "Origin",
                "Network",
                "Mask",
                "Next_Hop",
                "Metric",
                "LocPrf",
                "Weight",
                "Path",
                "Removed",
                "Src"
            ]
        )

    def update(self, pack, pubip_pref):
        bgp_pack = pack[BGPUpdate]
        while bgp_pack:
            # Console().print(Panel(Pretty(bgp_pack.fields)))
            path_attr = bgp_pack.path_attr
            if path_attr:
                org = None
                as_path = None
                next_hop = None
                med = 0
                lp = None
                for pattr in path_attr:
                    attr = pattr.attribute

                    if attr is None:
                        continue
                    if "ORIGIN" in attr.name:
                        org = attr.origin
                    elif "AS_PATH" in attr.name:
                        attr = BGPPAAS4Path(attr.original)

                        as_path = attr.segment_value + ["i"]
                    elif "NEXT_HOP" in attr.name:
                        next_hop = attr.next_hop
                    elif "MULTI_EXIT_DISC" in attr.name:
                        med = attr.med
                    elif "LOCAL_PREF" in attr.name:
                        lp = attr.local_pref
                as_ip_src = get_net_ip(pack[IP].src.split("/")[0], 24)
                # check if the network and next hop are in the table
                net=bgp_pack.nlri[0].prefix.split('/')[0]
                mask=bgp_pack.nlri[0].prefix.split('/')[1]
                query = (
                    f"Network=='{net}'"
                    + f" and Next_Hop=='{next_hop}'"
                )
                if len(self.table.query(query)) > 0:
                    # set the removed flag to true
                    self.table.loc[
                        self.table.query(
                            f"Network=='{net}' and Mask=='{bgp_pack.nlri[0].prefix.split('/')[1]}' and Next_Hop=='{next_hop}'"
                        ).index,
                        "Removed",
                    ] = True
                if len(self.table.query(f"Network=='{net}' and Src=='{pack[IP].src}'"))>0:
                    self.table.loc[
                        self.table.query(
                            f"Network=='{net}' and Src=='{pack[IP].src}'"
                        ).index,
                        "Removed",
                    ] = True
                # add the new route to the table
                self.table = pd.concat(
                    [
                        self.table,
                        pd.DataFrame(
                            [
                                {
                                    "selected": False,
                                    "Origin": "e" if as_ip_src == pubip_pref else "i",
                                    "Network": bgp_pack.nlri[0].prefix.split("/")[0],
                                    "Mask": bgp_pack.nlri[0].prefix.split("/")[1],
                                    "Next_Hop": (
                                        pack[IP].src
                                        if as_ip_src == pubip_pref
                                        else next_hop
                                    ),
                                    "Metric": med,
                                    "LocPrf": lp,
                                    "Weight": 0,
                                    "Path": as_path,
                                    "Removed": False,
                                    "Src": pack[IP].src,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
            # check if it has a payload
            if bgp_pack.payload:
                bgp_pack = bgp_pack.payload[BGPUpdate]
            else:
                break

    def to_rich_table(self, query="*"):
        table = Table()
        table.add_column("Selected")
        table.add_column("Origin")
        table.add_column("Network")
        table.add_column("Mask")
        table.add_column("Next Hop")
        table.add_column("Metric")
        table.add_column("LocPrf")
        table.add_column("Weight")
        table.add_column("Path")
        table.add_column("Removed")
        table.add_column("Src")
        for index, row in self.table.query(query).iterrows():
            table.add_row(
                str(row["selected"]),
                str(row["Origin"]),
                row["Network"],
                row["Mask"],
                row["Next_Hop"],
                str(row["Metric"]),
                str(row["LocPrf"]),
                str(row["Weight"]),
                str(row["Path"]),
                str(row["Removed"]),
                row["Src"],
                style=(
                    ("bold" if row["selected"] else "") + " red strike"
                    if row["Removed"]
                    else "green"
                ),
            )
        return table


console = Console()
file = os.path.join("MQ", "Fitxers-20240325", "Ex3-updates.pcapng")
capt = rdpcap(file)
ips = set()
for pack in capt:
    # pack=capt[0]
    # print the name of the interface
    # print(pack.name)
    ipsource = pack[IP].src
    ipdest = pack[IP].dst
    ips.add(ipsource)
    ips.add(ipdest)
    bgpu_pack = pack[BGPUpdate]
ips = list(ips)
ips.sort(key=ip_to_int)
console.print(ips)

ips_to_name = {
    "15.0.0.1": "R01",
    "15.0.0.2": "R02",
    "35.0.0.1": "R05",
    "35.0.0.2": "R04",
    "55.0.0.1": "R09",
    "55.0.0.2": "R07",
    "55.0.0.17": "R07",
    "55.0.0.18": "R08",
    "192.168.0.1": "R09",
    "192.168.0.2": "R01",
    "192.168.0.5": "R01",
    "192.168.0.6": "R07",
    "192.168.0.9": "R07",
    "192.168.0.10": "R02",
    "192.168.0.13": "R02",
    "192.168.0.14": "R03",
    "192.168.0.17": "R09",
    "192.168.0.18": "R06",
    "192.168.0.21": "R06",
    "192.168.0.22": "R08",
    "192.168.0.25": "R06",
    "192.168.0.26": "R05",
    "192.168.0.29": "R08",
    "192.168.0.30": "R05",
    "192.168.0.33": "R08",
    "192.168.0.34": "R04",
    "192.168.0.37": "R03",
    "192.168.0.38": "R04",
}

# for ip in ips:
#     id_router = IntPrompt.ask(f"Enter the id of the router with ip {ip}")
#     ips_to_name[ip] = "R" + str(id_router).rjust(2, "0")
routers = {}

for ip, router in ips_to_name.items():
    if router not in routers:
        routers[router] = {"table": BGP_table(), "ips": set()}
    routers[router]["ips"].add(ip)
pubip_pref = set()
ipsets = [data["ips"] for router, data in routers.items()]
pubip_pref = set([get_net_ip(ip, 24) for ip in list(ipsets[0])])
for ipset in ipsets:
    pubip_pref = pubip_pref.intersection(
        set([get_net_ip(ip, 24) for ip in list(ipset)])
    )
# console.print(ips_to_name)
# console.print(routers)
pubip_pref = list(pubip_pref)[0]
for n, pack in enumerate(capt):
    if n == 70:
        print("este")
    ipdest = pack[IP].dst
    print(n, ips_to_name[ipdest])
    routers[ips_to_name[ipdest]]["table"].update(pack, pubip_pref)
for router in sorted(list(routers.keys()), key=lambda x: int(x[1:])):
    console.print(
        Panel(
            routers[router]["table"].to_rich_table(query="Network=='15.0.0.0'"),
            title=router,
        )
    )
