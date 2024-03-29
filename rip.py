from scapy.all import rdpcap
from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.rip import RIP, RIPEntry
from scapy.utils import PcapReader
from rich.console import Console
import os
from Net.ip import get_net_ip,ip_to_int


def octet_to_int_mask(octet):
    # example 255.255.255.240 to /28
    return sum([bin(int(x)).count("1") for x in octet.split(".")])


def parse_rip_packet(packet, devs):
    ipsource = packet[IP].src
    ipdst = packet[IP].dst
    table = []
    # since the RIP entry is stored in the previous layer as a payload,
    # we can walk through the RIP entries
    for entry in get_packet_layers(packet[RIPEntry]):
        net = entry.addr
        mask = entry.mask
        metric = entry.metric
        table.append(
            [
                "R",
                net,
                octet_to_int_mask(mask),
                [120, metric + 1],
                ipsource,
                devs[ipsource],
            ]
        )
    return table


def generate_table(devs, rip_packets):
    table = []
    for packet in rip_packets:
        table.append(parse_rip_packet(packet, devs))
    return table


def get_packet_layers(packet):
    counter = 0
    while True:
        layer = packet.getlayer(counter)
        if layer is None:
            break

        yield layer
        counter += 1


def check_in_table(table, row):
    for n, trow in enumerate(table):
        if trow[1] == row[1] and trow[2] == row[2]:
            return True, n
    return False, -1


blocks = []
console = Console()
ex = 1
files = [
    os.path.join("MQ", "Fitxers-20240325", f)
    for f in os.listdir(os.path.join("MQ", "Fitxers-20240325"))
    if f.startswith(f"Ex{ex}")
]

devs = {}


# print(block._raw) #byte type raw data
console.print(devs)
table = []
console.print(files)
for file in files:
    data = rdpcap(
        file,
    )
    console.print(data)
    console.print(len(data))
    devs[data[0][IP].src] = os.path.basename(file).split(".")[0].split("-")[1]
    for pack in data:
        pack.show()
        for row in parse_rip_packet(pack, devs):
            intable, n = check_in_table(table, row)
            if intable:
                if table[n][3][1] > row[3][1]:
                    table[n] = row
            else:
                table.append(row)
# add the networks directly connected to the router
for dev in devs:
    table.append(["C", get_net_ip(dev, 28), 28, "directly", "connected", devs[dev]])
# sort the table by the network
table.sort(key=lambda x: ip_to_int(x[1]))
console.print(table)
console.print(devs)
