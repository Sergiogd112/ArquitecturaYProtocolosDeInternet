from rich.console import Console
from rich.prompt import Prompt
from rich.layout import Layout
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from Net import loaders
from .show import Show


class Configure:
    def __init__(self, scenario: str):
        self.console = Console()
        self.layout = Layout()
        self.scenario = scenario

    def run(self, net, stype):
        self.console.print("Configure scenario")
        while True:
            self.console.print("What do you want to configure?")
            opt = Prompt.ask(
                "Select an option",
                choices=[
                    "r",
                    "routers",
                    "b",
                    "briges",
                    "rt",
                    "routes",
                    "solver",
                    "l",
                    "load",
                    "q",
                    "quit",
                ],
            )
            if opt == "r" or opt == "routers":
                self.configure_routers(net)
            elif opt == "b" or opt == "bridges":
                self.configure_bridges(net)
            elif opt == "rt" or opt == "routes":
                self.configure_routes(net)
            elif opt == "solver":
                stype = self.configure_solver(stype)
            elif opt == "l" or opt == "load":
                self.load_scenario(net)
            elif opt == "q" or opt == "quit":
                return net, stype
            else:
                self.console.print("Invalid option")

    def configure_routers(self, net):
        self.console.print("Configure routers")
        while True:
            Show().show_routers(net)
            self.console.print("Select a router")
            router = Prompt.ask(
                "Select a router",
                choices=sorted(list(net.routers.keys())),
            )
            section = Prompt.ask(
                "Select a section",
                choices=["iface", "ospf", "bgp"],
            )
            Show().show_router(router, net.routers[router], True)
            if section == "iface":
                self.configure_iface(net, router)
            elif section == "ospf":
                self.configure_ospf(net, router)
            elif section == "bgp":
                self.configure_bgp(net, router)
            else:
                self.console.print("Invalid option")
            self.console.print("Do you want to configure another router?")
            opt = Prompt.ask(
                "Select an option",
                choices=["y", "yes", "n", "no"],
            )
            if opt in ["n", "no"]:
                break

    def configure_iface(self, net, router):
        self.console.print("Configure iface")
        while True:
            Show().show_router(router, net.routers[router], True)

            iface = Prompt.ask(
                "Select an iface",
                choices=["q", "quit"] + list(net.routers[router]["iface"].keys()),
            )
            if iface in ["q", "quit"]:
                return
            self.console.print("Selected iface: " + iface)
            opt = Prompt.ask(
                "Select an option", choices=["ip", "ospf", "bgp", "q", "quit"]
            )
            if opt in ["q", "quit"]:
                continue
            if opt == "ip":
                ip = Prompt.ask("Enter the ip/mask[10.0.0.3/24]:")
                self.console.print(
                    f"Setting iface {iface} with ip {ip} on router {router}"
                )
                net.set_ip(router, iface, ip, True)
            elif opt == "ospf":
                p2p = Prompt.ask(
                    "Is it a point-to-point link?", choices=["y", "yes", "n", "no"]
                )
                net.set_iface_ospf(router, iface, p2p, True)

    def configure_ospf(self, net, router):
        self.console.print("Configure ospf")
        while True:
            Show().show_router(router, net.routers[router], True)
            area = Prompt.ask(
                "Select an area",
                choices=["q", "quit", "c", "create"] + net.get_ospf_areas(),
            )
            if area in ["q", "quit"]:
                return
            if area in ["c", "create"]:
                area = Prompt.ask("Enter the area:")
            netip = Prompt.ask(
                "Enter the network ip/mask",
                choices=["all"] + net.get_netips_from_router(router),
            )
            if netip != "all":
                mask = net.bridges[net.get_brg_with_netip(netip)]["mask"]
                net.set_ospf(router, area, netip + "/" + str(mask), True)
                continue
            for netip in net.get_netips_from_router(router):
                mask = net.bridges[net.get_brg_with_netip(netip)]["mask"]

                net.set_ospf(router, area, netip + "/" + str(mask), True)

    def setup_bgp(self, net, router):
        asnum = Prompt.ask(
            "Enter the as number",
            choices=["q", "quit", "c", "create"] + net.get_asnums(),
        )
        if asnum in ["q", "quit"]:
            return
        if asnum in ["c", "create"]:
            asnum = Prompt.ask("Enter the as number:")
        router_id = Prompt.ask(
            "Enter the router id:",
            choices=["q", "quit"]
            + [ip.split("/")[0] for ip in net.get_router_ips(router)]
            + ["other"],
        )
        if router_id == "q" or router_id == "quit":
            return
        if router_id == "other":
            router_id = Prompt.ask("Enter the router id:")

        network = Prompt.ask(
            "Enter the network ip/mask", default=net.get_net_from_bgp_as(asnum)
        )
        net.set_bgp(router, asnum, router_id, network, True)

    def configure_bgp_route_map(self, net, router, neighbor):
        self.console.print("Configure bgp route map")
        while True:
            Show().show_router(router, net.routers[router], True)
            if "bgp" not in net.routers[router]:
                self.setup_bgp(net, router)
                continue
            opt = Prompt.ask("Do you want:", choices=["select", "create", "q", "quit"])
            if opt in ["q", "quit"]:
                return
            if opt == "create":
                name = Prompt.ask("Enter the name")
                net.add_bgp_route_map(router, neighbor, name, True)
                continue
            if opt == "select":
                name = Prompt.ask(
                    "Select a route map",
                    choices=net.get_bgp_route_maps(router) + ["q", "quit"],
                )
                if name in ["q", "quit"]:
                    return
                net.add_bgp_route_map(router, name, True)
                return

    def create_bgp_route_map(self, net, router):
        self.console.print("Create bgp route map")
        while True:
            Show().show_router(router, net.routers[router], True)
            if "bgp" not in net.routers[router]:
                self.setup_bgp(net, router)
                continue
            name = Prompt.ask("Enter the name")
            self.console.print(net.routers[router]["bgp"]["neighbor"])
            neighbor = Prompt.ask(
                "Select a neighbor",
                choices=["q", "quit"]
                + [
                    data["name"]
                    for nid, data in net.routers[router]["bgp"]["neighbor"].items()
                ]
                + list(net.routers[router]["bgp"]["neighbor"].keys()),
            )
            if neighbor in ["q", "quit"]:
                return
            in_out = Prompt.ask(
                "Select the direction", choices=["in", "out", "q", "quit"]
            )
            if in_out in ["q", "quit"]:
                return
            net.add_bgp_route_map(router, neighbor, name, in_out, True)
            opt = Prompt.ask(
                "Do you want to add a match?", choices=["y", "yes", "n", "no"]
            )
            if opt in ["n", "no"]:
                return
            self.add_bgp_route_map_match(net, router, name)

    def add_bgp_route_map_match(self, net, router, name):
        self.console.print("Add bgp route map match")
        while True:
            Show().show_router(router, net.routers[router], True)
            if "bgp" not in net.routers[router]:
                self.setup_bgp(net, router)
                continue
            opt = Prompt.ask("Select an ip range to match:")
            if opt in ["q", "quit"]:
                return
            self.console.print("Selected ip range: " + opt)
            table = Table(title="Match Types")
            table.add_column("Name")
            table.add_column("Definition")
            table.add_column("Range")
            table.add_row(
                "local-preference",
                Text(
                    "The local preference attribute is the second BGP attribute "
                    + "in the BGP best path selection algorithm. "
                    + "The local preference attribute is used to select the "
                    + "exit point from the local AS. "
                    + "The local preference attribute is a well-known discretionary attribute."
                ),
                "0-4294967295",
            )
            table.add_row(
                "metric",
                Text(
                    "The metric attribute is the third BGP attribute in the BGP "
                    + "best path selection algorithm. "
                    + "The metric attribute is used to select the exit point from the local AS. "
                    + "The metric attribute is a well-known discretionary attribute."
                ),
                "0-4294967295",
            )
            table.add_row(
                "weight",
                Text(
                    "The weight attribute is the fourth BGP attribute in the BGP "
                    + "best path selection algorithm. "
                    + "The weight attribute is used to select the exit point from the local AS. "
                    + "The weight attribute is a well-known discretionary attribute."
                ),
                "0-4294967295",
            )
            self.console.print(table, justify="center")
            loc_pref = Prompt.ask("Enter the local preference:")
            metric = Prompt.ask("Enter the metric:")
            weight = Prompt.ask("Enter the weight:")
            if loc_pref == "" or not loc_pref.isdigit():
                loc_pref = None
            if metric == "" or not metric.isdigit():
                metric = None
            if weight == "" or not weight.isdigit():
                weight = None
            net.add_bgp_route_map_match(
                router, name, opt, loc_pref, metric, weight, True
            )

    def setup_bgp_neighbor(self, net, router):
        self.console.print("Configure bgp neighbor")
        while True:
            Show().show_router(router, net.routers[router], True)
            if "bgp" not in net.routers[router]:
                self.setup_bgp(net, router)
                continue
            columns = Columns()

            adj = net.get_neighbors(router)
            if len(adj) == 0:
                self.console.print("No neighbors")
                return
            columns.add_renderable(Panel("- " + "\n- ".join(adj), title="Neighbors"))
            same_as = [
                x
                for x in net.get_routers_with_bgp_as(net.routers[router]["bgp"]["as"])
                if x != router
            ]
            columns.add_renderable(Panel("- " + "\n- ".join(same_as), title="Same AS"))
            columns.add_renderable(
                Panel("- " + "\n- ".join(net.routers.keys()), title="All")
            )
            columns.add_renderable(Panel("q, quit", title="Quit"))
            self.console.print(columns)
            neighbor = Prompt.ask(
                "Select a neighbor",
                choices=["q", "quit"] + list(net.routers.keys()),
                show_choices=False,
            )
            if neighbor in ["q", "quit"]:
                return
            if "bgp" not in net.routers[neighbor]:
                self.console.print("Neighbor has no bgp, setting up bgp for neighbor")
                self.setup_bgp(net, neighbor)
            net.add_bgp_neighbor(router, neighbor, True)
            if "bgp" not in net.routers[neighbor]:
                self.console.print(
                    "Neighbor has no bgp neighbor, setting up bgp neighbor for neighbor"
                )
                self.setup_bgp(net, neighbor)
            if router not in net.routers[neighbor]["bgp"]["neighbor"]:
                opt = Prompt.ask(
                    "Do you want to add the neighbor to the neighbor?",
                    choices=["y", "yes", "n", "no"],
                )
                if opt in ["y", "yes"]:
                    net.add_bgp_neighbor(neighbor, router, True)
            opt = Prompt.ask(
                "Do you want to configure a route map?",
                choices=["y", "yes", "n", "no"],
            )
            if opt in ["y", "yes"]:
                self.configure_bgp_route_map(net, router, neighbor)

    def configure_bgp(self, net, router):
        self.console.print("Configure bgp")
        while True:
            Show().show_router(router, net.routers[router], True)
            if "bgp" not in net.routers[router]:
                self.setup_bgp(net, router)
                continue
            opt = Prompt.ask(
                "Select an option",
                choices=["s", "setup", "n", "neighbor", "r", "route-map", "q", "quit"],
            )
            if opt in ["q", "quit"]:
                return
            if opt == "setup" or opt == "s":
                self.setup_bgp(net, router)
            elif opt == "neighbor" or opt == "n":
                self.setup_bgp_neighbor(net, router)
            elif opt == "route-map" or opt == "r":
                self.create_bgp_route_map(net, router)

    def configure_bridges(self, net):
        self.console.print("Configure bridges")
        while True:
            Show().show_bridges(net)
            self.console.print("Select a bridge")
            bridge = Prompt.ask(
                "Select a bridge",
                choices=["q", "quit"] + sorted(list(net.bridges.keys())),
            )
            if bridge in ["q", "quit"]:
                return
            section = Prompt.ask(
                "Select a section",
                choices=["netip", "connect", "ospf", "bgp", "q", "quit"],
            )
            if section == "netip":
                self.configure_brg_netip(net, bridge)
            elif section == "connect":
                self.configure_connect(net, bridge=bridge)
            elif section == "ospf":
                self.configure_ospf_bridge(net, bridge)
            elif section == "bgp":
                self.configure_bgp_bridge(net, bridge)
            elif section == "q":
                return
            else:
                self.console.print("Invalid option")

    def configure_brg_netip(self, net, bridge):
        self.console.print("Configure netip")
        while True:
            Show().show_bridge(bridge, net.bridges[bridge], True)
            netip = Prompt.ask(
                "Enter the network ip/mask", choices=net.get_netips_to_bridge(bridge)
            )
            net.set_bridge_netip(bridge, netip, apply=True)

    def configure_connect(self, net, bridge=None, router=None, iface=None):
        self.console.print("Configure connect")
        while True:
            if bridge:
                Show().show_bridge(bridge, net.bridges[bridge], True)
                router = Prompt.ask(
                    "Select a router",
                    choices=["q", "quit"] + list(net.routers.keys()),
                )
                if router in ["q", "quit"]:
                    return
                iface = Prompt.ask(
                    "Select an iface",
                    choices=["q", "quit"] + list(net.routers[router]["iface"].keys()),
                )
                if iface in ["q", "quit"]:
                    return
                net.set_bridge_connect(bridge, router, iface, apply=True)
            else:
                Show().show_router(router, net.routers[router], True)
                bridge = Prompt.ask(
                    "Select a bridge",
                    choices=["q", "quit"] + list(net.bridges.keys()),
                )
                if bridge in ["q", "quit"]:
                    return
                net.set_bridge_connect(bridge, router, iface, apply=True)

    def configure_routes(self, net):
        self.console.print("TODO: Configure routes")

    def configure_solver(self, stype):
        self.console.print("Configure scenario")
        stype = Prompt.ask("Select the type", choices=["static", "rip", "ospf", "bgp"])
        self.console.print("Selected type: " + stype)

        return stype

    def load_scenario(self, net):
        self.console.print("Loading scenario")
        opt = Prompt.ask(
            "Do you want to load from files or the current running config?",
            choices=["f", "files", "c", "config"],
        )
        if opt in ["f", "files"]:
            net.load_scenario(self.scenario)
        elif opt in ["c", "config"]:
            self.load_running(net)
        else:
            self.console.print("Invalid option")

    def load_running(self, net):
        self.console.print("Loading running config")
        while True:
            src = Prompt.ask(
                "Enter the source router",
                choices=[
                    "vtrc",
                    "vtyshrc",
                    "brctl",
                    "vtrt",
                    "vtyshrt",
                    "a",
                    "all",
                    "q",
                    "quit",
                ],
            )
            if src == "vtrc":
                net.load_running_config()
                Show().show_routers(net)
            elif src == "vtyshrc":
                net.load_running_config()
                Show().show_routers(net)
            elif src == "vtrt":
                net.load_vtyshrt()
                Show().show_routes(net)
            elif src == "vtyshrt":
                Show().show_routes(net)
                net.load_vtyshrt()
            elif src == "brctl":
                net.load_brctl_show()
                Show().show_bridges(net)
            elif src == "a" or src == "all":
                loaders.load_running_config(net)
                # Show().show_net(net)
                Show().show_routers(net)
                loaders.load_vtyshrt(net)
                Show().show_routes(net)
                loaders.load_brctl_show(net)
                Show().show_bridges(net)

            elif src in ["q", "quit"]:
                return
            else:
                self.console.print("Invalid option")

    def configure_ospf_bridge(self, net, bridge):
        self.console.print("Configure ospf")
        while True:
            Show().show_bridge(bridge, net.bridges[bridge], True)
            area = Prompt.ask(
                "Select an area",
                choices=["q", "quit", "c", "create"]
                + [x["area"] for _, x in net.bridges[bridge]["ospf"].items()],
            )
            if area in ["q", "quit"]:
                return
            if area in ["c", "create"]:
                area = Prompt.ask("Enter the area:")

            net.set_ospf_bridge(bridge, area, True)
            if len(net.bridges[bridge]["routers"]) == 2:
                p2p = Prompt.ask(
                    "Is it a point-to-point link?", choices=["y", "yes", "n", "no"]
                )
                net.set_ospf_bridge_p2p(bridge, p2p, True)

    def configure_bgp_bridge(self, net, bridge):
        pass
