import os

from rich.tree import Tree
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.pretty import Pretty
from rich.columns import Columns
import networkx as nx
from matplotlib import pyplot as plt

# from pyvis.network import Network
import re
import yaml
from Net.ip import *


colors = [
    "red",
    "green",
    "blue",
    "yellow",
    "cyan",
    "magenta",
    "white",
    "black",
    "bright_red",
    "bright_green",
    "bright_blue",
    "bright_yellow",
    "bright_cyan",
    "bright_magenta",
    "bright_white",
    "bright_black",
]


def convert_nested_single_line_to_dict(text, depth=0):
    parts = [part.strip() for part in text.split(":")]
    if len(parts) - depth > 2:
        return {
            parts[depth]: convert_nested_single_line_to_dict(
                ":".join(parts[depth + 1 :]), depth=depth + 1
            )
        }
    else:
        return {parts[0]: parts[1]}


def convert_router_to_dict(text, area):
    lines = text.split("\n")
    data = {"Area": area}
    link_data = []
    for line in lines:
        if "OSPF Router with ID" in line:
            continue
        if "Router Link States (Area" in line:
            continue
        if "Network Link States (Area" in line:
            continue
        if line.startswith("    Link connected to:"):
            link = {"Link connected to": line.split(": ")[1]}
            link_data.append(link)
        elif line.startswith("    "):
            key, value = line.strip().split(": ")
            link_data[-1][key] = value
        elif len(line.split(": ")) > 2:
            res = convert_nested_single_line_to_dict(line)
            data.update(res)

        elif line:
            key, value = line.split(": ")
            data[key.strip()] = value
    data["Links"] = link_data
    return data


def lsa_router_to_dict(text):
    data = {}
    area = text.split("Area")[1].split(")")[0].strip()
    routers = []
    for block in text.split("\n\n\n"):
        if not block:
            continue
        if "LS age" not in block:
            continue
        res = convert_router_to_dict(block, area)
        data.update({res["Advertising Router"]: res})
        routers.append(res["Advertising Router"])
    return data, routers, area


def convert_network_to_dict(text, area):
    lines = text.split("\n")
    data = {"Area": area}
    link_data = []
    for line in lines:
        if "OSPF Router with ID" in line:
            continue
        if "Net Link States (" in line:
            continue
        if line.startswith("        Attached Router:"):
            link = {"Attached Router": line.split(": ")[1]}
            link_data.append(link)
        elif line.startswith("    "):
            key, value = line.strip().split(": ")
            link_data[-1][key.stip()] = value
        elif len(line.split(": ")) > 2:
            res = convert_nested_single_line_to_dict(line)
            data.update(res)

        elif line:
            key, value = line.split(": ")
            data[key.strip()] = value
    data["Links"] = link_data
    data["Netip"] = get_net_ip(
        data["Link State ID"].split(" ")[0].strip(), int(data["Network Mask"][1:])
    )
    return data


def lsa_network_to_dict(text):
    data = {}
    area = text.split("Area")[1].split(")")[0].strip()
    nets = []
    for block in text.split("\n\n"):
        if not block:
            continue
        if "LS age" not in block:
            continue
        res = convert_network_to_dict(block, area)
        data.update({res["Netip"]: res})
        nets.append(res["Netip"])
    return data, nets, area


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


def load_console(routers, nets, areas, areas_routers, areas_nets):
    nrouters = len(routers)
    setrouters_names = []
    area_router_names = {}  #
                            # "0.0.0.0": ["R03", "R04", "R05", "R06"],
                            # "0.0.0.1": ["R04", "R06", "R07", "R08"],
                            # "0.0.0.2": ["R01", "R02", "R03"],
    ids_to_names = {}
    for area in areas:
        print(f"Area: {area}")
        routers_id_area = [
            "R" + r.rjust(2, "0") for r in Prompt.ask("Routers").split(" ")
        ]
        area_router_names[area] = routers_id_area
    Console().print(dict_to_tree(area_router_names, "Area routers"))
    # create a dict with the frontier routers with a tuple of the areas as key
    frontier_routers_names = {}
    frontier_routers_names_array = []
    non_frontier_routers_names = {}
    for n, area in enumerate(areas):
        router_names = area_router_names[area]
        for router_name in router_names:
            for area2 in areas[n + 1 :]:
                router_names2 = area_router_names[area2]
                if router_name in router_names2:
                    if (area, area2) not in frontier_routers_names:
                        frontier_routers_names[(area, area2)] = []
                    frontier_routers_names[(area, area2)].append(router_name)
                    frontier_routers_names_array.append(router_name)
            if router_name not in frontier_routers_names_array:
                if area not in non_frontier_routers_names:
                    non_frontier_routers_names[area] = []
                non_frontier_routers_names[area].append(router_name)
    Console().print(dict_to_tree(frontier_routers_names, "Frontier routers"))
    Console().print(dict_to_tree(non_frontier_routers_names, "Non frontier routers"))
    # find the frontier routers from the lsa
    frontier_routers_ids = {}
    frontier_routers_ids_array = []
    non_frontier_routers_ids = {}
    for n, area in enumerate(areas):
        for router_name in areas_routers[area]:
            for area2 in areas[n + 1 :]:
                if router_name in areas_routers[area2]:
                    if (area, area2) not in frontier_routers_ids:
                        frontier_routers_ids[(area, area2)] = []
                    frontier_routers_ids[(area, area2)].append(router_name)
                    frontier_routers_ids_array.append(router_name)
            if router_name not in frontier_routers_ids_array:
                if area not in non_frontier_routers_ids:
                    non_frontier_routers_ids[area] = []
                non_frontier_routers_ids[area].append(router_name)
    Console().print(dict_to_tree(frontier_routers_ids, "Frontier routers ids"))
    Console().print(dict_to_tree(non_frontier_routers_ids, "Non frontier routers ids"))
    for frontier, _ in frontier_routers_ids.items():
        if len(frontier_routers_ids[frontier]) == 0:
            continue
        if len(frontier_routers_ids[frontier]) == 1:
            routers[frontier_routers_ids[frontier][0]]["Frontier"] = True
            routers[frontier_routers_names[frontier][0]] = routers[
                frontier_routers_ids[frontier][0]
            ]
            del routers[frontier_routers_ids[frontier][0]]
            areas_routers[frontier[0]].remove(frontier_routers_ids[frontier][0])
            areas_routers[frontier[1]].remove(frontier_routers_ids[frontier][0])
            areas_routers[frontier[0]].append(frontier_routers_names[frontier][0])
            areas_routers[frontier[1]].append(frontier_routers_names[frontier][0])
            ids_to_names[frontier_routers_ids[frontier][0]] = frontier_routers_names[
                frontier
            ][0]
            setrouters_names.append(frontier_routers_names[frontier][0])
        else:
            for router_name in frontier_routers_ids[frontier]:
                routers[router_name]["Frontier"] = True
                if "Candidates" not in routers[router_name]:
                    routers[router_name]["Candidates"] = set(
                        frontier_routers_names[frontier]
                    )
                # intersection
                routers[router_name]["Candidates"].intersection(
                    frontier_routers_names[frontier]
                )
                if len(routers[router_name]["Candidates"]) == 1:
                    candidate = routers[router_name]["Candidates"].pop()
                    routers[candidate] = routers[router_name]
                    del routers[router_name]
                    areas_routers[frontier[0]].remove(router_name)
                    areas_routers[frontier[1]].remove(router_name)
                    areas_routers[frontier[0]].append(candidate)
                    areas_routers[frontier[1]].append(candidate)
                    setrouters_names.append(candidate)
                    ids_to_names[router_name] = candidate
    for area, router_ids in non_frontier_routers_ids.items():
        if len(router_ids) == 0:
            continue
        if len(router_ids) == 1:
            routers[router_ids[0]]["Frontier"] = False
            routers[non_frontier_routers_names[area][0]] = routers[router_ids[0]]
            del routers[router_ids[0]]
            areas_routers[area].remove(router_ids[0])
            areas_routers[area].append(non_frontier_routers_names[area][0])
            setrouters_names.append(non_frontier_routers_names[area][0])
            ids_to_names[router_ids[0]] = non_frontier_routers_names[area][0]
        else:
            for router_id in router_ids:
                routers[router_id]["Frontier"] = False
                if "Candidates" not in routers[router_id]:
                    routers[router_id]["Candidates"] = set(
                        non_frontier_routers_names[area]
                    )
                # intersection
                routers[router_id]["Candidates"].intersection(
                    non_frontier_routers_names[area]
                )
                if len(routers[router_id]["Candidates"]) == 1:
                    candidate = routers[router_id]["Candidates"].pop()
                    routers[candidate] = routers[router_id]
                    del routers[router_id]
                    areas_routers[area].remove(router_id)
                    areas_routers[area].append(candidate)
                    setrouters_names.append(candidate)
                    ids_to_names[router_id] = candidate
    if setrouters_names == nrouters:
        print("All routers set")

        show_routers(routers, areas_routers)
        return routers,ids_to_names
    stub_routers_names = {}#"0.0.0.0": ["R04"], "0.0.0.1": ["R04"], "0.0.0.2": ["R02"]
    non_stub_routers_names = {}#"0.0.0.0": ["R06"],
                                # "0.0.0.1": ["R06", "R07", "R08"],
                                # "0.0.0.2": ["R01"],
    for n, area in enumerate(areas):
        print(f"Area: {area}")
        router_names = [
            "R" + r.rjust(2, "0") for r in Prompt.ask("Stub routers").split(" ")
        ]
        stub_routers_names[area] = [r for r in router_names if r not in setrouters_names]
        non_stub_routers_names[area] = [
            r for r in area_router_names[area] if r not in router_names and r not in setrouters_names
        ]
    Console().print(stub_routers_names)
    Console().print(non_stub_routers_names)
    stub_routers_ids = {}
    non_stub_routers_ids = {}
    p2p_routers_ids = {}
    non_p2p_routers_ids = {}
    for n, area in enumerate(areas):
        for router_id in areas_routers[area]:
            if "R" in router_id:
                continue
            p2p = 0
            stub = 0
            for link in routers[router_id]["Links"]:
                if "Stub" in link["Link connected to"]:
                    stub += 1
                if "point" in link["Link connected to"]:
                    p2p += 1
            stub = stub - p2p
            if stub > 0:
                if area not in stub_routers_ids:
                    stub_routers_ids[area] = []
                stub_routers_ids[area].append(router_id)
            else:
                if area not in non_stub_routers_ids:
                    non_stub_routers_ids[area] = []
                non_stub_routers_ids[area].append(router_id)
            if p2p > 0:
                if area not in p2p_routers_ids:
                    p2p_routers_ids[area] = []
                p2p_routers_ids[area].append(router_id)
            else:
                if area not in non_p2p_routers_ids:
                    non_p2p_routers_ids[area] = []
                non_p2p_routers_ids[area].append(router_id)
    for area, router_ids in non_stub_routers_ids.items():
        if len(router_ids) == 0:
            continue
        if len(router_ids) == 1:
            routers[router_ids[0]]["Stub"] = False
            routers[non_stub_routers_names[area][0]] = routers[router_ids[0]]
            del routers[router_ids[0]]
            areas_routers[area].remove(router_ids[0])
            areas_routers[area].append(non_stub_routers_names[area][0])
            setrouters_names.append(non_stub_routers_names[area][0])
            ids_to_names[router_ids[0]] = non_stub_routers_names[area][0]
        else:
            for router_id in router_ids:
                if router_id in ids_to_names:
                    areas_routers[area].remove(router_id)
                    areas_routers[area].append(ids_to_names[router_id])
                    continue
                routers[router_id]["Stub"] = False
                if "Candidates" not in routers[router_id]:
                    routers[router_id]["Candidates"] = set(non_stub_routers_names[area])
                # intersection
                routers[router_id]["Candidates"].intersection(
                    non_stub_routers_names[area]
                )
                if len(routers[router_id]["Candidates"]) == 1:
                    candidate = routers[router_id]["Candidates"].pop()
                    routers[candidate] = routers[router_id]
                    del routers[router_id]
                    areas_routers[area].append(candidate)
                    setrouters_names.append(candidate)
                    ids_to_names[router_id] = candidate
    for area, router_ids in stub_routers_ids.items():
        if len(router_ids) == 0:
            continue
        if len(router_ids) == 1:
            if router_ids[0] not in ids_to_names:
                
                routers[router_ids[0]]["Stub"] = True
                routers[stub_routers_names[area][0]] = routers[router_ids[0]]
                del routers[router_ids[0]]
                setrouters_names.append(stub_routers_names[area][0])

            areas_routers[area].remove(router_ids[0])
            areas_routers[area].append(stub_routers_names[area][0])
            ids_to_names[router_ids[0]] = stub_routers_names[area][0]
        else:
            for router_id in router_ids:
                routers[router_id]["Stub"] = True
                if "Candidates" not in routers[router_id]:
                    routers[router_id]["Candidates"] = set(stub_routers_names[area])
                # intersection
                routers[router_id]["Candidates"].intersection(stub_routers_names[area])
                if len(routers[router_id]["Candidates"]) == 1:
                    candidate = routers[router_id]["Candidates"].pop()
                    routers[candidate] = routers[router_id]
                    del routers[router_id]
                    areas_routers[area].remove(router_id)
                    areas_routers[area].append(candidate)
                    setrouters_names.append(candidate)
                    ids_to_names[router_id] = candidate
    for router, data in routers.items():
        if "Stub" not in data:
            data["Stub"] = False
        if "Frontier" not in data:
            data["Frontier"] = False
        if "R" in router:
            continue
        for cand in list(data["Candidates"]):
            if cand in setrouters_names:
                data["Candidates"].remove(cand)
        if len(data["Candidates"]) == 1:
            candidate = data["Candidates"].pop()
            routers[candidate] = data
            del routers[router]
            areas_routers[data["Area"]].remove(router)
            areas_routers[data["Area"]].append(candidate)
            setrouters_names.append(candidate)
            ids_to_names[router] = candidate
    if setrouters_names == nrouters:
        print("All routers set")
        show_routers(routers, areas_routers)
        return routers,ids_to_names
    numports_names = {}
    for area,router_names in area_router_names.items():
        for router in router_names:
            if router in setrouters_names:
                continue
            n=IntPrompt.ask(f"Number of ports for {router}")
            if area not in numports_names:
                numports_names[area] = {}
            if n not in numports_names[area]:
                numports_names[area][n] = []
            numports_names[area][n].append(router)
        
    numports_ids = {}
    for router, data in routers.items():
        if router in setrouters_names:
            continue
        n=sum([1 if "point" not in link["Link connected to"] else -1 for link in data["Links"]])
        if data["Area"] not in numports_ids:
            numports_ids[data["Area"]] = {}
        if n not in numports_ids[data["Area"]]:
            numports_ids[data["Area"]][n] = []
        numports_ids[data["Area"]][n].append(router)
    Console().print(numports_ids)
    for area,data in numports_ids.items():
        for n, router_ids in data.items():
            if len(router_ids) == 0:
                continue
            if len(router_ids) == 1:
                routers[numports_names[area][n][0]] = routers[router_ids[0]]
                del routers[router_ids[0]]
                areas_routers[area].remove(router_ids[0])
                areas_routers[area].append(numports_names[area][n][0])
                setrouters_names.append(numports_names[area][n][0])
                ids_to_names[router_ids[0]] = numports_names[area][n][0]
            else:
                for router_id in router_ids:
                    if "Candidates" not in routers[router_id]:
                        routers[router_id]["Candidates"] = set(numports_names[area][n])
                    # intersection
                    routers[router_id]["Candidates"].intersection(
                        set(numports_names[area][n])
                    )
                    if len(routers[router_id]["Candidates"]) == 1:
                        candidate = routers[router_id]["Candidates"].pop()
                        routers[candidate] = routers[router_id]
                        del routers[router_id]
                        areas_routers[area].append(candidate)
                        setrouters_names.append(candidate)
                        ids_to_names[router_id] = candidate
    show_routers(routers, areas_routers)
    Console().print(ids_to_names)
    return routers,ids_to_names
def show_routers(routers, area_routers):
    columns = Columns()
    for n, (area, rnames) in enumerate(area_routers.items()):
        subcolumns = Columns()
        for rname in rnames:
            tree = dict_to_tree(routers[rname], rname)
            subcolumns.add_renderable(Panel(tree, title=rname))
        columns.add_renderable(Panel(subcolumns, title=area, border_style=colors[n]))

    Console().print(Panel(columns, title="Routers", border_style="magenta"))


def show_nets(nets, area_nets):
    columns = Columns()
    for n, (area, net_names) in enumerate(area_nets.items()):
        subcolumns = Columns()
        for net_name in net_names:
            tree = dict_to_tree(nets[net_name], net_name)
            subcolumns.add_renderable(Panel(tree, title=net_name))
        columns.add_renderable(
            Panel(subcolumns, title="Area: " + area, border_style=colors[-n - 4])
        )
    Console().print(Panel(columns, title="Networks", border_style="green"))


def run():

    console = Console()

    folder = os.path.join("MQ", "2324QP", "Ex-OSPF-20240403")

    routers = {}
    nets = {}
    console.log(f"Reading files from {folder}")
    area_routers = {}
    area_nets = {}
    for file in os.listdir(folder):
        with open(os.path.join(folder, file)) as f:
            if "router" in file:
                res, router_names, area = lsa_router_to_dict(f.read())
                area_routers[area] = router_names
                for name, data in res.items():
                    routers[name] = data
            elif "network" in file:
                res, nets_names, area = lsa_network_to_dict(f.read())
                area_nets[area] = nets_names
                for name, data in res.items():
                    nets[name] = data
            elif "summary" in file:
                pass
            elif "resum" in file:
                pass
            else:
                print("Unknown file type")
                print(file)
            # print(f.read())
    columns = Columns()

    show_routers(routers, area_routers)
    show_nets(nets, area_nets)
    # print("=====================================")
    # routers,ids_to_names=load_console(routers, nets, list(area_routers.keys()), area_routers, area_nets)
    # show_nets(nets, area_nets)
    # print("=====================================")
    # print(ids_to_names)
    # show_routers(routers, area_routers)

run()
