import os
from typing import Tuple
from rich.console import Console
from rich.panel import Panel

from .route import RouteTable
from . import Net
from .ip import get_net_ip


def read_scenario(scenario: str, pract="") -> "Net":
    """
    Reads a scenario file and returns a 'Net' object representing the network.

    Args:
        scenario (str): The name of the scenario file.
        pract (str, optional): The name of the practice directory. Defaults to "".

    Returns:
        Net: A 'Net' object representing the network.

    Raises:
        FileNotFoundError: If no config directory is found.

    """
    routers = {}
    if pract == "":
        path = "/home/api/practiques/" + scenario.split("-")[0] + "/" + scenario
    else:
        path = "/home/api/practiques/" + pract + "/" + scenario
    # if this path is not a directory set it to:

    if not os.path.isdir(path):
        path = os.path.join("practiques", scenario.split("-")[0], scenario)
    el = ""
    if "A" not in pract:
        # Console().print(path)
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
            Console().print(Panel(config))
            if "config" in config and "bak" not in config:
                with open(
                    os.path.join(path, el, config), "r", encoding="utf-8"
                ) as file:
                    contents = file.read()
                name, conf = lxc_to_router(contents)
                routers[name] = conf
    else:
        for el in os.listdir(os.path.join(path)):
            if os.path.isfile(os.path.join(path, el, "config")):
                with open(
                    os.path.join(path, el, "config"), "r", encoding="utf-8"
                ) as file:
                    contents = file.read()
                name, conf = lxc_to_router(contents)
                routers[name] = conf
    return Net(routers)


def lxc_to_router_new(text: str) -> Tuple[str, dict]:
    """
    Parses the given text to extract the UTS name and network configuration
    of an LXC container and returns them as a tuple.

    Args:
        text (str): The text containing the LXC container configuration.

    Returns:
        Tuple[str, Dict]: A tuple containing the UTS name and network configuration
        of the LXC container.

    Example:
        text = '''
        lxc.uts.name = mycontainer

        # Network configuration
        lxc.network.name = eth0
        lxc.network.link = br0
        lxc.network.address = 192.168.1.100/24
        '''

        lxc_to_router_new(text)  # Returns: ('mycontainer', {
            'iface': {
                'eth0': {
                    'brg': 'br0',
                    'ip': '192.168.1.100/24'}
                    }
                }
            )
    """
    text = text.strip()
    # get the uts.name
    utsname = text.split("lxc.uts.name = ")[1].split("\n")[0]
    # get the network configuration
    netconf = text.split("# Network configuration")[1].split("\n\n")
    netcondict = {"iface": {}}
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
    return utsname, netcondict


def lxc_to_router_old(text: str) -> Tuple[str, dict]:
    """
    Parses the given text to extract the UTS name and network configuration
    of a router in an LXC container.

    Args:
        text (str): The text containing the LXC configuration.

    Returns:
        Tuple[str, dict]: A tuple containing the UTS name and a dictionary
        representing the network configuration.

    Example:
        text = '''
        lxc.utsname = myrouter
        # Network configuration

        eth0.name = eth0
        eth0.link = br0
        eth0.address = 192.168.1.100/24

        eth1.name = eth1
        eth1.link = br1
        '''

        lxc_to_router_old(text) will return:
        ('myrouter', {
            'iface': {
                'eth0': {
                    'brg': 'br0',
                    'ip': '192.168.1.100/24'
                },
                'eth1': {
                    'brg': 'br1'
                }
            }
        })
    """
    text = text.strip()
    # get the uts.name
    utsname = text.split("lxc.utsname = ")[1].split("\n")[0]
    # get the network configuration
    netconf = text.split("# Network configuration")[1].split("\n\n")
    netcondict = {"iface": {}}
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
    return utsname, netcondict


def lxc_to_router(text: str) -> Tuple[str, dict]:
    """
    Converts LXC configuration to router configuration.

    Args:
        text (str): The LXC configuration text.

    Returns:
        Tuple[str, dict]: A tuple containing the router name and its configuration.

    Raises:
        None

    """
    if "uts.name" in text:
        return lxc_to_router_new(text)
    else:
        return lxc_to_router_old(text)


def read_vtyshrc(net, contents: str) -> Tuple[int, dict]:
    """
    Read the contents of a vtyshrc file and extract interface and OSPF configuration.

    Args:
        net: The network object.
        contents: The contents of the vtyshrc file.

    Returns:
        A tuple containing the number of changes made and a dictionary
        representing the configuration.

    Example:
        Example contents:
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
        block = block.strip()
        if "" == block:
            continue

        if "interface" in block:
            name = block.split("interface ")[1].split("\n")[0]
            if name not in res["iface"]:
                res["iface"][name] = {"brg": None}
                changes += 1
            for line in block.split("\n")[1:]:
                if "ip address" in line:
                    address = line.split("ip address ")[1].split("\n")[0]
                    res["iface"][name] = {"brg": None, "ip": address}
                    changes += 1
                elif "ip ospf" in line:
                    res["iface"][name]["ospf"] = line.split("ip ospf ")[1].split("\n")[
                        0
                    ]
                    changes += 1
        elif "router ospf" in block:
            if "ospf" not in res:
                res["ospf"] = []
            for line in block.split("\n")[1:]:
                if "network" not in line:
                    continue
                area = line.split("area ")[1].split("\n")[0]
                net = line.split("network ")[1].split(" ")[0]
                res["ospf"] += [{"area": area, "network": net}]
                changes += 1
        elif "router rip" in block:
            if "rip" not in res:
                res["rip"] = {}
            for line in block.split("\n")[1:]:
                opt, port = line.strip().split(" ")
                if port not in res["rip"]:
                    res["rip"][port] = {}
                res["rip"][port][opt] = True
                changes += 1
        elif "router bgp" in block:
            if "bgp" not in res:
                res["bgp"] = {}
            bgp_as = block.split("router bgp ")[1].split("\n")[0].strip()
            res["bgp"]["as"] = bgp_as
            for line in block.split("\n")[1:]:
                if "id" in line:
                    res["bgp"]["id"] = line.strip().split("id ")[1].split("\n")[0]
                    changes += 1
                if "network" in line:
                    net = line.strip().split("network ")[1].split("\n")[0]
                    res["bgp"]["network"] = net
                    changes += 1
                if "neighbor" in line:
                    neigh = line.strip().split("neighbor ")[1].split(" ")[0]
                    if "neighbor" not in res["bgp"] or res["bgp"]["neighbor"] is None:
                        res["bgp"]["neighbor"] = {}
                    if neigh not in res["bgp"]["neighbor"]:
                        res["bgp"]["neighbor"][neigh] = {}
                    if "remote-as" in line:
                        remote = line.strip().split("remote-as ")[1].split("\n")[0]
                        res["bgp"]["neighbor"][neigh]["remote"] = remote
                    if "route-map" in line:
                        print(line.strip())
                        rmap = line.strip().split("route-map ")[1].split("\n")[0]
                        rname = line.strip().split("route-map ")[1].split(" ")[0]
                        inout = line.strip().split("route-map ")[1].split(" ")[1]
                        res["bgp"]["neighbor"][neigh]["rmap"] = {
                            "name": rname,
                            "inout": inout,
                        }
                    changes += 1
        elif "access-list" in block:
            if "acl" not in res:
                res["acl"] = []
            for line in block.split("\n"):
                if "permit" in line:
                    acl = (
                        line.split("access-list ")[1]
                        .split("\n")[0]
                        .split(" ")[0]
                        .strip()
                    )
                    permit = line.split("permit ")[1].split("\n")[0].strip()

                    res["acl"] += [{"name": acl, "permit": permit}]
                    changes += 1
        elif "route-map" in block:
            if "rmap" not in res:
                res["rmap"] = {}
            rname = block.split("route-map ")[1].split(" ")[0].strip()
            permit = block.split("route-map ")[1].split(" ")[1].strip()
            res["rmap"][rname] = {"permit": permit}
            for line in block.split("\n")[1:]:
                if "match" in line:
                    if "match" not in res["rmap"][rname]:
                        res["rmap"][rname]["match"] = {}
                    rmap = line.split("route-map ")[1].split("\n")[0].strip()
                    match = line.split("match ")[1].split("\n")[0].strip()
                    res["rmap"][rname]["match"][match] = {}
                    changes += 1
                if "set" in line:
                    res["rmap"][rname]["match"][match] = {
                        line.split(" ")[1].strip(): line.split(" ")[2].strip()
                    }

    return changes, res


def load_vtyshrt(net):
    """
    Loads the VTYSH routes for each router in the network.

    Args:
        net (Network): The network object.

    Returns:
        None
    """
    for router, _ in net.routers.items():
        # Console().print(f"Loading VTYSH routes for {router}")
        console_out = os.popen(
            f"lxc-attach -n {router} -- vtysh -c 'show ip route'"
        ).read()
        if router not in net.routes:
            net.routes[router] = RouteTable()
        net.routes[router].loads_vtysh_routes(console_out)


def load_running_config_router(net, router):
    # get the vtysh running config
    consoleout = (
        os.popen(f"lxc-attach -n {router} -- vtysh -c 'show running'")
        .read()
        .split("end")[0]
    )
    ch, res = read_vtyshrc(net, consoleout)
    if ch < 1:
        return
    if "ospf" in res:
        net.routers[router]["ospf"] = res["ospf"]

    for iface, con in res["iface"].items():
        if len(con) < 1:
            continue
        if iface not in net.routers[router]["iface"].keys():
            net.routers[router]["iface"][iface] = con
        else:
            net.routers[router]["iface"][iface] = {
                "brg": net.routers[router]["iface"][iface]["brg"],
                "ip": (
                    con["ip"]
                    if "ip" in con and con["ip"] is not None
                    else (
                        net.routers[router]["iface"][iface]["ip"]
                        if "ip" in net.routers[router]["iface"][iface]
                        else None
                    )
                ),
            }
        if "ospf" in con:
            net.routers[router]["iface"][iface]["ospf"] = con["ospf"]
            netip = get_net_ip(con["ip"])
            for i, row in enumerate(net.routers[router]["ospf"]):
                if row["network"] == netip:
                    net.routers[router]["ospf"][i]["p2p"] = True
        if "bgp" in res:
            net.routers[router]["bgp"] = res["bgp"]
            if "neighbor" in res["bgp"]:
                for id, neigh in res["bgp"]["neighbor"].items():
                    net.routers[router]["bgp"]["neighbor"][id]["name"] = (
                        net.get_router_with_ip(id)
                    )


def load_running_config(net):
    """
    Loads the running configuration of the network.

    Args:
        net (Network): The network object.

    Returns:
        None
    """
    for router, _ in net.routers.items():
        load_running_config_router(net, router)

    for router,conf  in net.routers.items():
        if "bgp" in conf and "neighbor" in conf["bgp"]:
            for id, neigh in conf["bgp"]["neighbor"].items():
                net.routers[router]["bgp"]["neighbor"][id]["name"] = (
                    net.get_router_with_ip(id)
                )
    # Console().print(self.routers)
    net.bridges = net.generate_bridges(net.routers)


def load_brctl_show(net):
    """
    Loads the output of the 'brctl show' command and updates the network object accordingly.

    Args:
        net: The network object to update.

    Returns:
        None
    """
    consoleout = os.popen("brctl show").read()
    pbrg = None
    for line in consoleout.split("\n")[1:]:
        brg = line.split("\t")[0]
        if brg == "":
            brg = pbrg
        if brg not in net.bridges.keys():
            net.bridges[brg] = {"routers": [], "devcount": 0}
        # Console().print(line)
        try:
            router, iface = line.split("\t")[-1].split("-")
        except ValueError:
            continue
        if brg not in net.bridges.keys():
            net.bridges[brg] = {"routers": [router], "devcount": 3}
        else:
            net.bridges[brg]["routers"].append(router)
            net.bridges[brg]["routers"] = sorted(list(set(net.bridges[brg]["routers"])))
            net.bridges[brg]["devcount"] += 1
        if router not in net.routers.keys():
            net.routers[router] = {"iface": {iface: {"brg": brg}}}
        else:
            net.routers[router]["iface"][iface]["brg"] = brg
        pbrg = brg


def read_scenario_subconfigs(net, escenario: str, sub: str):
    """
    Reads the sub-configurations for a given scenario and updates the network object accordingly.

    Args:
        net (Network): The network object to update.
        escenario (str): The name of the scenario.
        sub (str): The sub-configuration identifier.

    Raises:
        FileNotFoundError: If no config directory is found.

    Returns:
        None
    """
    path = "/home/api/practiques/" + escenario.split("-")[0] + "/" + escenario
    # if this path is not a directory set it to:
    if not os.path.isdir(path):
        path = os.path.join("practiques", escenario.split("-")[0], escenario)
    # Console().print(path)
    for el in os.listdir(path):
        if "config" in el and "bak" not in el and os.path.isdir(os.path.join(path, el)):
            break
    else:
        raise FileNotFoundError("No config directory found")
    for file in os.listdir(os.path.join(path, el)):
        if sub in file:
            router = file.split("_")[1]
            # Console().print(router)
            with open(os.path.join(path, el, file), "r", encoding="utf-8") as file:
                contents = file.read()
            ch, res = read_vtyshrc(net, contents)
            # Console().print(router, ch)
            # Console().print(res)
            if ch < 1:
                continue

            for port, conf in res["iface"].items():
                # Console().print(port)
                # Console().print(conf)

                if len(conf) < 1:
                    continue

                if router not in net.routers.keys():
                    net.routers[router] = {"iface": {port: {"brg": conf["brg"]}}}
                if port not in net.routers[router]["iface"].keys():
                    net.routers[router]["iface"][port] = {"brg": conf["brg"]}
                if len(conf) <= 1:
                    net.routers[router]["iface"][port]["brg"] = net.routers[router][
                        "iface"
                    ][port]["brg"]
                else:
                    net.routers[router]["iface"][port] = {
                        "brg": net.routers[router]["iface"][port]["brg"],
                        "ip": (
                            conf["ip"]
                            if "ip" in conf and conf["ip"] is not None
                            else (
                                net.routers[router]["iface"][port]["ip"]
                                if "ip" in net.routers[router]["iface"][port]
                                else None
                            )
                        ),
                    }
            if "ospf" in res:
                net.routers[router]["ospf"] = res["ospf"]
    net.bridges = net.generate_bridges(net.routers)
