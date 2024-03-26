#!/usr/bin/python3

import os
from rich.tree import Tree
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.columns import Columns
from Net.ip import *


class Node:
    def __init__(self, name: str, next=[]):
        self.name = name
        self.next = next

    def to_tree(self):
        tree = Tree(self.name)
        for n in self.next:
            tree.add(n.to_tree())
        return tree
    def __repr__(self):
        return self.name+"->"+str("\n ".join([str(x) for x in self.next]))

def net_from_console():
    routers = {}
    nets = {}
    nrouter = IntPrompt.ask("Enter number of routers", default=1)
    ippref = Prompt.ask("Enter IP prefix", default="10.0.")
    submask = IntPrompt.ask("Enter subnet mask", default=24)
    for i in range(nrouter):
        router = Prompt.ask(f"Enter router name {i+1}", default=f"R{i+1}")
        routers[router] = {}
        nint = IntPrompt.ask(f"Enter number of interfaces for {router}", default=1)
        for j in range(nint):
            intf = Prompt.ask(f"Enter interface name {j+1}", default=f"eth{j}")
            routers[router][intf] = {}
            ip = ippref + Prompt.ask(
                f"Enter IP address for {intf} after {ippref}",
                default=f"10.0.{i+1}.{j+1}",
            )
            routers[router][intf]["ip"] = ip
            if get_net_ip(ip, submask) in nets:
                routers[router][intf]["neigh"] = nets[get_net_ip(ip, submask)][1:]
                continue
            neighs = Prompt.ask(f"Enter neighbors for {intf}", default="")
            if neighs and "," in neighs:
                neigh = neighs.split(",")
            elif neighs and " " in neighs:
                neigh = neighs.split()
            else:
                neigh = [neighs]
            nets[get_net_ip(ip, submask)] = [router] + neigh
            routers[router][intf]["neigh"] = neigh
        Console().print(routers[router])
        Console().print(dict_to_tree(routers[router], router))
    npc = IntPrompt.ask("Enter number of PCs", default=1)
    for i in range(npc):
        pc = Prompt.ask(f"Enter PC name {i+1}", default=f"PC{i+1}")
        routers[pc] = {}
        routers[pc]["eth0"] = {}
        ip = ippref + Prompt.ask(
            f"Enter IP address for {pc}", default=f"10.0.{i+1}.101"
        )
        routers[pc]["eth0"]["ip"] = ip
        neigh = Prompt.ask(f"Enter neighbors for {pc}", default="").split()
        routers[pc]["eth0"]["neigh"] = neigh
        Console().print(routers[pc])
        Console().print(dict_to_tree(routers[pc], pc))
    return routers


def pc_from_console(routers, nets):
    npc = IntPrompt.ask("Enter number of PCs", default=1)
    ippref = Prompt.ask("Enter IP prefix", default="10.0.")
    submask = IntPrompt.ask("Enter subnet mask", default=24)

    for i in range(npc):
        if i < 10:
            pc = Prompt.ask(f"Enter PC name {i+1}", default=f"PC0{i+1}")
        else:
            pc = Prompt.ask(f"Enter PC name {i+1}", default=f"PC{i+1}")
        routers[pc] = {}
        routers[pc]["eth0"] = {}
        ip = ippref + Prompt.ask(
            f"Enter IP address for {pc}", default=f"10.0.{i+1}.101"
        )
        routers[pc]["eth0"]["ip"] = ip
        routers[pc]["eth0"]["netip"] = get_net_ip(ip, submask) + "/" + str(submask)
        neigh = Prompt.ask(
            f"Enter neighbors for {pc}",
            default=" ".join(
                nets[get_net_ip(ip, submask) + "/" + str(submask)]["members"]
            ),
        ).split()
        for neigth in neigh:
            if neigth not in routers:
                continue
            for iface, info in routers[neigth].items():
                if info["netip"] == get_net_ip(ip, submask) + "/" + str(submask):
                    routers[neigth][iface]["neigh"].append(pc)
                    break
        nets[get_net_ip(ip, submask) + "/" + str(submask)]["members"].append(pc)
        routers[pc]["eth0"]["neigh"] = neigh
        Console().print(routers[pc])
        Console().print(dict_to_tree(routers[pc], pc))
    return routers, nets


def dict_to_tree(data: dict, name: str) -> Tree:
    tree = Tree(name)
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            subtree = dict_to_tree(value, str(key))
            tree.add(subtree)
        elif isinstance(value, list) or isinstance(value, tuple):
            subtree = list_to_tree(value, str(key))
            tree.add(subtree)
        else:
            tree.add(str(key) + ": " + str(value))
    # Console().print(tree)
    return tree


def list_to_tree(data: list, name: str) -> Tree:
    tree = Tree(name)
    for n, item in enumerate(data):
        if isinstance(item, dict):
            subtree = dict_to_tree(item, str(n))
            tree.add(subtree)
        elif isinstance(item, list) or isinstance(item, tuple):
            subtree = list_to_tree(item, str(n))
            tree.add(subtree)
        else:
            tree.add(str(n) + ": " + str(item))
    return tree


def read_mroute(data, nets, name):

    # Given multicast routing table
    interface_dict = {}
    data = data.strip()

    # Given dictionary of interfaces
    blocks = data.split("\n\n")
    # generate an array mapping idx to interface using the first block
    vif_map = []
    # print(blocks[0])
    index = blocks[0].split("\n")[2:]
    lindex = len(index)
    for n, line in enumerate(index):
        row = line.strip().split()
        # idx = int(row[0])
        ifaceip = row[1]
        netip = row[2]
        if len(netip.split(".")) < 4:
            netip = netip.replace("/", ".0/")
        if n < lindex - 1:
            interface_dict["eth" + str(n)] = {
                "ip": ifaceip,
                "pim": {},
                "neigh": [],
                "netip": netip,
            }
            if netip not in nets:
                nets[netip] = {"members": []}
            nets[netip]["members"].append(name)
            vif_map.append("eth" + str(n))
        else:
            interface_dict["virt"] = {"ip": ifaceip, "pim": {}}
            vif_map.append("virt")
    sources = set()
    for block in blocks[1:]:
        # print(block)
        if "oifs" not in block:
            continue
        gtype = block.split("\n")[2].replace("-", "").strip()
        # print(name)
        ipsource = block.split("\n")[3].strip().split()[0].strip()
        source = (ipsource, block.split("\n")[3].strip().split()[1].strip())
        sources.add(source)
        for param in block.split("\n")[4:]:
            # print(param)
            row = param.split()[2].strip()
            # print(row)
            for n, char in enumerate(row):
                if char != ".":
                    # print(vif_map[n])
                    # print(interface_dict[vif_map[n]]["pim"])
                    if source not in interface_dict[vif_map[n]]["pim"]:
                        interface_dict[vif_map[n]]["pim"][source] = ""
                    interface_dict[vif_map[n]]["pim"][source] += char
                    if char == "I" and n < len(vif_map) - 1:
                        if source not in nets[interface_dict[vif_map[n]]["netip"]]:
                            nets[interface_dict[vif_map[n]]["netip"]][source] = {
                                "in": False
                            }
                        nets[interface_dict[vif_map[n]]["netip"]][source]["in"] = True
                    if char == "o" and n < len(vif_map) - 1:
                        if source not in nets[interface_dict[vif_map[n]]["netip"]]:
                            nets[interface_dict[vif_map[n]]["netip"]][source] = {
                                "out": False
                            }
                        nets[interface_dict[vif_map[n]]["netip"]][source]["out"] = True
                    # print(interface_dict[vif_map[n]]["pim"])
    Console().print(dict_to_tree(interface_dict, "Interfaces"))
    # print(sources)
    return interface_dict, sources, nets


def read_mroutes(path):
    with open(path, "r") as f:
        data = f.read().strip()
    blocks = data.split("\n\n\n\n")
    sources = set()
    nets = {}
    routers = {}
    for block in blocks:
        rname = block.split("\n")[0].strip().split("#")[0]

        print("Router", rname)
        if rname not in routers:
            routers[rname] = {}
        routers[rname], tsources, nets = read_mroute(
            "\n".join(block.split("\n")[1:]) + "\n", nets, rname
        )
        sources.update(tsources)
    # print(sources)
    for net in nets:
        for member in nets[net]["members"]:
            for iface, info in routers[member].items():
                if info["netip"] == net:
                    routers[member][iface]["neigh"] = [
                        mem for mem in nets[net]["members"] if mem != member
                    ]
                    break
    return routers, list(sources), nets


def print_routers(routers):
    columns = Columns()
    for router in routers:
        columns.add_renderable(
            Panel(
                dict_to_tree(routers[router], router), border_style="blue", title=router
            )
        )
    Console().print(columns)


def traverse_tree(routers, nets, source, current, depth=0):
    if depth > 10:
        print("Depth limit reached")
        return Node(current)
    if "PC" in current:
        if (
            nets[routers[current]["eth0"]["netip"]][source]["out"]
            and source[0] != routers[current]["eth0"]["ip"]
        ):
            return Node(current)
        if (
            nets[routers[current]["eth0"]["netip"]][source]["in"]
            and source[0] == routers[current]["eth0"]["ip"]
        ):
            next = []
            for neigh in routers[current]["eth0"]["neigh"]:
                if "R" in neigh:
                    print(neigh)
                    for iface, info in routers[neigh].items():
                        Console().print(info)
                        if current in info["neigh"] and "I" in info["pim"][source]:
                            next.append(
                                traverse_tree(routers, nets, source, neigh, depth + 1)
                            )
                            break
                elif (
                    "PC" in neigh
                    and nets[routers[neigh]["eth0"]["netip"]][source]["out"]
                ):
                    next.append(traverse_tree(routers, nets, source, neigh, depth + 1))
            return Node(current, next)
    else:
        next = []
        for iface, info in routers[current].items():
            if "virt" in iface:
                if "I" in info["pim"][source]:
                    continue
                if "o" in info["pim"][source]:
                    next.append(Node("RP"))
            else:
                if "I" in info["pim"][source]:
                    continue
                if "o" in info["pim"][source]:
                    for neigh in routers[current]["eth0"]["neigh"]:
                        if "R" in neigh:
                            for iface, info in routers[neigh].items():
                                if (
                                    current in info["neigh"]
                                    and "I" in info["pim"][source]
                                ):
                                    next.append(
                                        traverse_tree(
                                            routers, nets, source, neigh, depth + 1
                                        )
                                    )
                                    break
                        elif (
                            "PC" in neigh
                            and nets[routers[neigh]["eth0"]["netip"]][source]["out"]
                        ):
                            next.append(
                                traverse_tree(routers, nets, source, neigh, depth + 1)
                            )
        return Node(current, next)


def generate_tree(routers, sources, nets):
    # Find the shared trees and the source trees
    # print_routers(routers)
    sips = [x[0] for x in sources]
    pcsources = []
    for dev, conf in routers.items():
        if "PC" not in dev:
            continue
        print(dev)
        for iface, info in conf.items():
            if info["ip"] in sips:
                for n, sip in enumerate(sips):
                    if sip == info["ip"]:
                        source = sources[n]
                        break
                print(iface, info)
                pcsources.append((dev, iface, source))
                break
    trees = []
    for source in pcsources:
        print(source)
        tree = traverse_tree(
            routers,
            nets,
            str(source[2]).replace("'",'"'),
            source[0],
        )
        trees.append(tree)
        Console().print(tree)

    return pcsources, trees


def test():
    routers = {
        "R01": {
            "eth0": {
                "ip": "10.0.2.1",
                "pim": {},
                "neigh": ["R05"],
                "netip": "10.0.2.0/24",
            },
            "eth1": {
                "ip": "10.0.4.1",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "jo",
                    '("10.0.16.101", "239.1.1.1")': "p",
                },
                "neigh": ["R02"],
                "netip": "10.0.4.0/24",
            },
            "eth2": {
                "ip": "10.0.5.1",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "jo",
                    '("10.0.16.101", "239.1.1.1")': "p",
                },
                "neigh": ["R06"],
                "netip": "10.0.5.0/24",
            },
            "virt": {
                "ip": "10.0.2.1",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "I",
                    '("10.0.16.101", "239.1.1.1")': "I",
                },
            },
        },
        "R02": {
            "eth0": {
                "ip": "10.0.3.2",
                "pim": {'("10.0.16.101", "239.1.1.1")': "I"},
                "neigh": ["R05"],
                "netip": "10.0.3.0/24",
            },
            "eth1": {
                "ip": "10.0.4.2",
                "pim": {'("INADDR_ANY", "239.1.1.1")': "I"},
                "neigh": ["R01"],
                "netip": "10.0.4.0/24",
            },
            "eth2": {
                "ip": "10.0.6.2",
                "pim": {},
                "neigh": ["R07"],
                "netip": "10.0.6.0/24",
            },
            "eth3": {
                "ip": "10.0.12.2",
                "pim": {},
                "neigh": ["R03"],
                "netip": "10.0.12.0/24",
            },
            "eth4": {
                "ip": "10.0.17.2",
                "pim": {'("10.0.16.101", "239.1.1.1")': "jo"},
                "neigh": ["R06"],
                "netip": "10.0.17.0/24",
            },
            "eth5": {
                "ip": "10.0.18.2",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "jo",
                    '("10.0.16.101", "239.1.1.1")': "o",
                },
                "neigh": ["R08"],
                "netip": "10.0.18.0/24",
            },
            "virt": {"ip": "10.0.3.2", "pim": {}},
        },
        "R03": {
            "eth0": {
                "ip": "10.0.12.3",
                "pim": {},
                "neigh": ["R02"],
                "netip": "10.0.12.0/24",
            },
            "eth1": {
                "ip": "10.0.14.3",
                "pim": {},
                "neigh": ["R08", "PC05"],
                "netip": "10.0.14.0/24",
            },
            "eth2": {
                "ip": "10.0.15.3",
                "pim": {},
                "neigh": ["R04"],
                "netip": "10.0.15.0/24",
            },
            "virt": {"ip": "10.0.12.3", "pim": {}},
        },
        "R04": {
            "eth0": {
                "ip": "10.0.11.4",
                "pim": {'("10.0.16.101", "239.1.1.1")': "jo"},
                "neigh": ["R05"],
                "netip": "10.0.11.0/24",
            },
            "eth1": {
                "ip": "10.0.15.4",
                "pim": {},
                "neigh": ["R03"],
                "netip": "10.0.15.0/24",
            },
            "eth2": {
                "ip": "10.0.16.4",
                "pim": {
                    '("10.0.16.102", "239.1.1.1")': "I",
                    '("10.0.16.101", "239.1.1.1")': "I",
                },
                "neigh": ["PC01", "PC02"],
                "netip": "10.0.16.0/24",
            },
            "virt": {
                "ip": "10.0.11.4",
                "pim": {
                    '("10.0.16.102", "239.1.1.1")': "jo",
                    '("10.0.16.101", "239.1.1.1")': "jp",
                },
            },
        },
        "R05": {
            "eth0": {
                "ip": "10.0.2.5",
                "pim": {},
                "neigh": ["R01"],
                "netip": "10.0.2.0/24",
            },
            "eth1": {
                "ip": "10.0.3.5",
                "pim": {'("10.0.16.101", "239.1.1.1")': "jo"},
                "neigh": ["R02"],
                "netip": "10.0.3.0/24",
            },
            "eth2": {
                "ip": "10.0.11.5",
                "pim": {'("10.0.16.101", "239.1.1.1")': "I"},
                "neigh": ["R04"],
                "netip": "10.0.11.0/24",
            },
            "virt": {"ip": "10.0.2.5", "pim": {}},
        },
        "R06": {
            "eth0": {
                "ip": "10.0.5.6",
                "pim": {'("INADDR_ANY", "239.1.1.1")': "I"},
                "neigh": ["R01"],
                "netip": "10.0.5.0/24",
            },
            "eth1": {
                "ip": "10.0.7.6",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "lo",
                    '("10.0.16.101", "239.1.1.1")': "lo",
                },
                "neigh": ["PC03"],
                "netip": "10.0.7.0/24",
            },
            "eth2": {
                "ip": "10.0.8.6",
                "pim": {},
                "neigh": ["R07"],
                "netip": "10.0.8.0/24",
            },
            "eth3": {
                "ip": "10.0.9.6",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "jo",
                    '("10.0.16.101", "239.1.1.1")': "jo",
                },
                "neigh": ["R09"],
                "netip": "10.0.9.0/24",
            },
            "eth4": {
                "ip": "10.0.17.6",
                "pim": {'("10.0.16.101", "239.1.1.1")': "I"},
                "neigh": ["R02"],
                "netip": "10.0.17.0/24",
            },
            "virt": {"ip": "10.0.5.6", "pim": {}},
        },
        "R07": {
            "eth0": {
                "ip": "10.0.6.7",
                "pim": {},
                "neigh": ["R02"],
                "netip": "10.0.6.0/24",
            },
            "eth1": {
                "ip": "10.0.8.7",
                "pim": {},
                "neigh": ["R06"],
                "netip": "10.0.8.0/24",
            },
            "eth2": {
                "ip": "10.0.10.7",
                "pim": {},
                "neigh": ["R09", "PC04"],
                "netip": "10.0.10.0/24",
            },
            "eth3": {
                "ip": "10.0.13.7",
                "pim": {},
                "neigh": ["R08"],
                "netip": "10.0.13.0/24",
            },
            "virt": {"ip": "10.0.6.7", "pim": {}},
        },
        "R08": {
            "eth0": {
                "ip": "10.0.13.8",
                "pim": {},
                "neigh": ["R07"],
                "netip": "10.0.13.0/24",
            },
            "eth1": {
                "ip": "10.0.14.8",
                "pim": {'("INADDR_ANY", "239.1.1.1")': "lo"},
                "neigh": ["R03", "PC05"],
                "netip": "10.0.14.0/24",
            },
            "eth2": {
                "ip": "10.0.18.8",
                "pim": {'("INADDR_ANY", "239.1.1.1")': "I"},
                "neigh": ["R02"],
                "netip": "10.0.18.0/24",
            },
            "virt": {"ip": "10.0.13.8", "pim": {}},
        },
        "R09": {
            "eth0": {
                "ip": "10.0.9.9",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "I",
                    '("10.0.16.101", "239.1.1.1")': "I",
                },
                "neigh": ["R06"],
                "netip": "10.0.9.0/24",
            },
            "eth1": {
                "ip": "10.0.10.9",
                "pim": {
                    '("INADDR_ANY", "239.1.1.1")': "lo",
                    '("10.0.16.101", "239.1.1.1")': "lo",
                },
                "neigh": ["R07", "PC04"],
                "netip": "10.0.10.0/24",
            },
            "virt": {"ip": "10.0.9.9", "pim": {}},
        },
        "PC01": {
            "eth0": {
                "ip": "10.0.16.101",
                "netip": "10.0.16.0/24",
                "neigh": ["R04", "PC02"],
            }
        },
        "PC02": {
            "eth0": {
                "ip": "10.0.16.102",
                "netip": "10.0.16.0/24",
                "neigh": ["R04", "PC01"],
            }
        },
        "PC03": {
            "eth0": {"ip": "10.0.7.103", "netip": "10.0.7.0/24", "neigh": ["R06"]}
        },
        "PC04": {
            "eth0": {
                "ip": "10.0.10.104",
                "netip": "10.0.10.0/24",
                "neigh": ["R07", "R09"],
            }
        },
        "PC05": {
            "eth0": {
                "ip": "10.0.14.105",
                "netip": "10.0.14.0/24",
                "neigh": ["R03", "R08"],
            }
        },
    }
    nets = {
        "10.0.2.0/24": {"members": ["R01", "R05"]},
        "10.0.4.0/24": {
            "members": ["R01", "R02"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": True},
        },
        "10.0.5.0/24": {
            "members": ["R01", "R06"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": True},
        },
        "10.0.3.0/24": {
            "members": ["R02", "R05"],
            '("10.0.16.101", "239.1.1.1")': {"in": True, "out": True},
        },
        "10.0.6.0/24": {"members": ["R02", "R07"]},
        "10.0.12.0/24": {"members": ["R02", "R03"]},
        "10.0.17.0/24": {
            "members": ["R02", "R06"],
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": True},
        },
        "10.0.18.0/24": {
            "members": ["R02", "R08"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": True},
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": False},
        },
        "10.0.14.0/24": {
            "members": ["R03", "R08", "PC05"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": False},
        },
        "10.0.15.0/24": {"members": ["R03", "R04"]},
        "10.0.11.0/24": {
            "members": ["R04", "R05"],
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": True},
        },
        "10.0.16.0/24": {
            "members": ["R04", "PC01", "PC02"],
            '("10.0.16.102", "239.1.1.1")': {"in": True, "out": False},
            '("10.0.16.101", "239.1.1.1")': {"in": True, "out": False},
        },
        "10.0.7.0/24": {
            "members": ["R06", "PC03"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": False},
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": False},
        },
        "10.0.8.0/24": {"members": ["R06", "R07"]},
        "10.0.9.0/24": {
            "members": ["R06", "R09"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": True},
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": True},
        },
        "10.0.10.0/24": {
            "members": ["R07", "R09", "PC04"],
            '("INADDR_ANY", "239.1.1.1")': {"out": True, "in": False},
            '("10.0.16.101", "239.1.1.1")': {"out": True, "in": False},
        },
        "10.0.13.0/24": {"members": ["R07", "R08"]},
    }
    sources = [
        ("10.0.16.102", "239.1.1.1"),
        ("10.0.16.101", "239.1.1.1"),
        ("INADDR_ANY", "239.1.1.1"),
    ]
    console = Console()

    # console.print(dict_to_tree(routers, "Network"), style="bold magenta")
    # net2 = net_from_console()
    # console.print(dict_to_tree(net2, "Network"), style="bold magenta")
    # console.print(net2)
    # routers, sources, nets = read_mroutes(
    #     os.path.join("MQ", "Fitxers-20240325", "Ex4-mroute.txt")
    # )
    # print_routers(routers)
    print(sources)
    # Console().print(nets)
    # routers, nets = pc_from_console(routers, nets)
    # Console().print(nets)
    # Console().print(routers)
    print_routers(routers)
    print(generate_tree(routers, sources, nets))


test()
