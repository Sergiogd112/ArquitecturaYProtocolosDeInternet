#!/usr/bin/python3

import os
from rich.tree import Tree
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from Net.ip import *


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


def dict_to_tree(data: dict, name: str) -> Tree:
    tree = Tree(name)
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            subtree = dict_to_tree(value, key)
            tree.add(subtree)
        elif isinstance(value, list) or isinstance(value, tuple):
            subtree = list_to_tree(value, key)
            tree.add(subtree)
        else:
            tree.add(key + ": " + str(value))
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


def read_mroute(path):
    # example of mroute file:
    # Virtual Interface Table
    #  Vif  Local-Address    Subnet               Thresh   Flags          Neighbors
    #    0  10.0.3.2         10.0.3/24            1        PIM            10.0.3.5
    #    1  10.0.4.2         10.0.4/24            1        DR PIM         10.0.4.1
    #    2  10.0.6.2         10.0.6/24            1        PIM            10.0.6.7
    #    3  10.0.12.2        10.0.12/24           1        PIM            10.0.12.3
    #    4  10.0.17.2        10.0.17/24           1        PIM            10.0.17.6
    #    5  10.0.18.2        10.0.18/24           1        PIM            10.0.18.8
    #    6  10.0.3.2         register_vif0        1

    # Multicast Routing Table
    #  Source          Group           RP-addr         Flags
    # ---------------------------(*,G)----------------------------
    #  INADDR_ANY      239.1.1.1       10.0.2.1        WC RP CACHE
    # Joined   oifs: .....j.
    # Pruned   oifs: .......
    # Leaves   oifs: .......
    # Asserted oifs: .......
    # Outgoing oifs: .....o.
    # Incoming     : .I.....

    # TIMERS:  Entry   JP   RS Assert VIFS:  0  1  2  3  4  5  6
    #            185     40    0    0          0  0  0  0  0  185  0
    # ---------------------------(S,G)----------------------------
    #  10.0.16.101     239.1.1.1       10.0.2.1        SPT CACHE SG
    # Joined   oifs: ....j..
    # Pruned   oifs: .......
    # Leaves   oifs: .......
    # Asserted oifs: .......
    # Outgoing oifs: ....oo.
    # Incoming     : I......

    # TIMERS:  Entry   JP   RS Assert VIFS:  0  1  2  3  4  5  6
    #            190    40    0    0         0 0 0 0 185 0 0
    # --------------------------(*,*,RP)--------------------------
    # Number of Groups: 1
    # Number of Cache MIRRORs: 2

    # Given multicast routing table
    multicast_routing_table = """
    Source          Group           RP-addr         Flags
    ---------------------------(*,G)----------------------------
    INADDR_ANY      239.1.1.1       10.0.2.1        WC RP CACHE
    Joined   oifs: .....j.             
    Pruned   oifs: .......             
    Leaves   oifs: .......             
    Asserted oifs: .......             
    Outgoing oifs: .....o.             
    Incoming     : .I.....             

    TIMERS:  Entry   JP   RS Assert VIFS:  0  1  2  3  4  5  6
            185     40    0    0          0  0  0  0  0  185  0
    ---------------------------(S,G)----------------------------
    10.0.16.101     239.1.1.1       10.0.2.1        SPT CACHE SG
    Joined   oifs: ....j..             
    Pruned   oifs: .......             
    Leaves   oifs: .......             
    Asserted oifs: .......             
    Outgoing oifs: ....oo.             
    Incoming     : I......             

    TIMERS:  Entry   JP   RS Assert VIFS:  0  1  2  3  4  5  6
            190    40    0    0         0 0 0 0 185 0 0
    --------------------------(*,*,RP)--------------------------
    Number of Groups: 1
    Number of Cache MIRRORs: 2
    """

    # Given dictionary of interfaces
    interface_dict = {
        "eth0": {"ip": "10.0.3.2", "neigh": ["R05"]},
        "eth1": {"ip": "10.0.12.2", "neigh": ["R03"]},
        "eth2": {"ip": "10.0.18.2", "neigh": ["R08"]},
        "eth3": {"ip": "10.0.6.2", "neigh": ["R07"]},
        "eth4": {"ip": "10.0.17.2", "neigh": ["R06"]},
        "eth5": {"ip": "10.0.4.2", "neigh": ["R01"]},
    }

        # Function to parse (*,G) and (S,G) sub-tables
    def parse_sub_table(sub_table):
        lines = sub_table.strip().split('\n')
        data = {}
        data['type'] = lines[0].strip()
        data['parameters'] = {}
        for line in lines[1:]:
            if line.strip() == "":
                continue
            elif 'TIMERS:' in line:
                data['timers'] = line.strip().split()[2:]
            else:
                key, value = line.strip().split(':')
                data['parameters'][key.strip()] = value.strip()
        return data

    # Function to merge multicast routing data with interface data
    def merge_data(mroute_data, interface_data):
        for interface, details in interface_data.items():
            if 'ip' in details and 'neigh' in details:
                ip = details['ip']
                if ip in mroute_data:
                    mroute_data[ip]['interface'] = interface
                    mroute_data[ip]['neighbors'] = details['neigh']
        return mroute_data

    # Parse multicast routing table
    mroute_data = {}
    sub_tables = multicast_routing_table.split('--------------------------')

    # Parse (*,G) sub-table
    _g_sub_table = sub_tables[0]
    sg_sub_table = sub_tables[1]
    _rp_sub_table = sub_tables[2:]
    mroute_data.update(parse_sub_table(_g_sub_table))
    mroute_data.update(parse_sub_table(sg_sub_table))

    # Merge with interface data
    merged_data = merge_data(mroute_data, interface_dict)

    # Print or save the result
    for ip, details in merged_data.items():
        print(f"IP: {ip}")
        print(f"Interface: {details['interface']}")
        print(f"Neighbors: {', '.join(details['neighbors'])}")
        print(f"Joined: {details['parameters'].get('Joined', 'N/A')}")
        print(f"Pruned: {details['parameters'].get('Pruned', 'N/A')}")
        print(f"Leaves: {details['parameters'].get('Leaves', 'N/A')}")
        print(f"Asserted: {details['parameters'].get('Asserted', 'N/A')}")
        print(f"Outgoing: {details['parameters'].get('Outgoing', 'N/A')}")
        print(f"Incoming: {details['parameters'].get('Incoming', 'N/A')}")
        print("\n")


    # Printing parameters for each interface
    for route in multicast_routes:
        print(f"Type: {route['type']}")
        print(f"Source: {route['source']}")
        print(f"Group: {route['group']}")
        print(f"RP Address: {route['rp_addr']}")
        print(f"Flags: {route['flags']}")
        print("Parameters for each interface:")
        for key, value in interface_dict.items():
            print(f"Interface: {key}")
            if route.get(key.lower()):
                print(f"Joined: {route[key.lower()]}")
            else:
                print("Not joined")
        print("\n")


def test():
    routers = {
        "R1": {
            "eth0": {"ip": "10.0.2.1", "neigh": ["R05"]},
            "eth1": {"ip": "10.0.4.1", "neigh": ["R02"]},
            "eth2": {"ip": "10.0.5.1", "neigh": ["R06"]},
        },
        "R2": {
            "eth0": {"ip": "10.0.3.2", "neigh": ["R05"]},
            "eth1": {"ip": "10.0.12.2", "neigh": ["R03"]},
            "eth2": {"ip": "10.0.18.2", "neigh": ["R08"]},
            "eth3": {"ip": "10.0.6.2", "neigh": ["R07"]},
            "eth4": {"ip": "10.0.17.2", "neigh": ["R06"]},
            "eth5": {"ip": "10.0.4.2", "neigh": ["R01"]},
        },
        "R3": {
            "eth0": {"ip": "10.0.15.3", "neigh": ["R04"]},
            "eth1": {"ip": "10.0.14.3", "neigh": ["R08,PC05"]},
            "eth2": {"ip": "10.0.12.3", "neigh": ["R02"]},
        },
        "R4": {
            "eth0": {"ip": "10.0.16.4", "neigh": ["PC01,PC02"]},
            "eth1": {"ip": "10.0.15.4", "neigh": ["R03"]},
            "eth2": {"ip": "10.0.11.4", "neigh": ["R05"]},
        },
        "R5": {
            "eth0": {"ip": "10.0.11.5", "neigh": ["R04"]},
            "eth1": {"ip": "10.0.3.5", "neigh": ["R02"]},
            "eth2": {"ip": "10.0.2.5", "neigh": ["R01"]},
        },
        "R6": {
            "eth0": {"ip": "10.0.5.6", "neigh": ["R01"]},
            "eth1": {"ip": "10.0.17.6", "neigh": ["R02"]},
            "eth2": {"ip": "10.0.8.6", "neigh": ["R07"]},
            "eth3": {"ip": "10.0.9.6", "neigh": ["R09"]},
            "eth4": {"ip": "10.0.7.6", "neigh": ["PC03"]},
        },
        "R7": {
            "eth0": {"ip": "10.0.6.7", "neigh": ["R02"]},
            "eth1": {"ip": "10.0.13.7", "neigh": ["R08"]},
            "eth2": {"ip": "10.0.10.7", "neigh": ["R09", "PC04"]},
            "eth3": {"ip": "10.0.8.7", "neigh": ["R06"]},
        },
        "R8": {
            "eth0": {"ip": "10.0.14.8", "neigh": ["R03", "PC05"]},
            "eth1": {"ip": "10.0.13.8", "neigh": ["R07"]},
            "eth2": {"ip": "10.0.18.8", "neigh": ["R02"]},
        },
        "R9": {
            "eth0": {"ip": "10.0.9.9", "neigh": ["R06"]},
            "eth1": {"ip": "10.0.10.9", "neigh": ["R07", "PC04"]},
        },
        "PC1": {"eth0": {"ip": "10.0.16.101", "neigh": ["R04", "PC02"]}},
        "PC2": {"eth0": {"ip": "10.0.16.102", "neigh": ["R04", "PC01"]}},
        "PC3": {"eth0": {"ip": "10.0.7.103", "neigh": ["R06"]}},
        "PC4": {"eth0": {"ip": "10.0.10.104", "neigh": ["R09", "R07"]}},
    }
    console = Console()

    console.print(dict_to_tree(routers, "Network"), style="bold magenta")
    net2 = net_from_console()
    console.print(dict_to_tree(net2, "Network"), style="bold magenta")
    console.print(net2)


# test()
read_mroute("mroute.txt")
