from rich.console import Console
from rich.prompt import Prompt
from rich.layout import Layout
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
            match opt:
                case "r":
                    self.configure_routers(net)
                case "routers":
                    self.configure_routers(net)
                case "b":
                    self.configure_bridges(net)
                case "bridges":
                    self.configure_bridges(net)
                case "rt":
                    self.configure_routes(net)
                case "routes":
                    self.configure_routes(net)
                case "solver":
                    stype = self.configure_solver(stype)
                case "l":
                    self.load_scenario(net)
                case "load":
                    self.load_scenario(
                        net,
                    )
                case "q":
                    return net, stype
                case "quit":
                    return net, stype
                case _:
                    self.console.print("Invalid option")

    def configure_routers(self, net):
        self.console.print("Configure routers")
        while True:
            Show().show_routers(net)
            self.console.print("Select a router")
            router = Prompt.ask(
                "Select a router",
                choices=net.routers.keys(),
            )
            section = Prompt.ask(
                "Select a section",
                choices=["iface", "ospf", "bgp"],
            )
            Show().show_router(net, router, net.routers[router], True)
            match section:
                case "iface":
                    self.configure_iface(net, router)
                case "ospf":
                    self.configure_ospf(net, router)
                case "bgp":
                    self.configure_bgp(net, router)
                case _:
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
            Show().show_router(net, router, net.routers[router], True)

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
            match opt:
                case "ip":
                    ip = Prompt.ask("Enter the ip/mask[10.0.0.3/24]:")
                    self.console.print(
                        f"Setting iface {iface} with ip {ip} on router {router}"
                    )
                    net.set_ip(router, iface, ip, True)
                case "ospf":
                    p2p = Prompt.ask(
                        "Is it a point-to-point link?", choices=["y", "yes", "n", "no"]
                    )
                    net.set_iface_ospf(router, iface, p2p, True)

    def configure_ospf(self, net, router):
        self.console.print("Configure ospf")
        while True:
            Show().show_router(net, router, net.routers[router], True)
            area = Prompt.ask(
                "Select an area",
                choices=["q", "quit", "c", "create"]
                        + [x["area"] for x in net.routers[router]["ospf"]],
            )
            if area in ["q", "quit"]:
                return
            if area in ["c", "create"]:
                area = Prompt.ask("Enter the area:")
            netip = Prompt.ask(
                "Enter the network ip/mask", choices=["all"] + net.get_netips_from_router(router)
            )
            if netip != "all":
                mask = net.bridges[net.get_brg_with_netip(netip)]["mask"]
                net.set_ospf(router, area, netip + "/" + str(mask), True)
                continue
            for netip in net.get_netips_from_router(router):
                mask = net.bridges[net.get_brg_with_netip(netip)]["mask"]

                net.set_ospf(router, area, netip + "/" + str(mask), True)

    def configure_bgp(self, net, router):
        self.console.print("TODO: Configure bgp")

    def configure_bridges(self, net):
        self.console.print("Configure bridges")
        while True:
            Show().show_bridges(net)
            self.console.print("Select a bridge")
            bridge = Prompt.ask(
                "Select a bridge",
                choices=["q", "quit"] + list(net.bridges.keys()),
            )
            if bridge in ["q", "quit"]:
                return
            section = Prompt.ask(
                "Select a section",
                choices=["netip", "connect", "ospf", "bgp", "q", "quit"],
            )
            match section:
                case "netip":
                    self.configure_brg_netip(net, bridge)
                case "connect":
                    self.configure_connect(net, bridge=bridge)
                case "ospf":
                    self.configure_ospf_bridge(net, bridge)
                case "bgp":
                    self.configure_bgp_bridge(net, bridge)
                case "q":
                    return
                case _:
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
                Show().show_router(net, router, net.routers[router], True)
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
                choices=["vtrc", "vtyshrc", "brctl", "vtrt", "vtyshrt","a","all", "q", "quit"],
            )
            match src:
                case "vtrc":
                    net.load_running_config()
                case "vtyshrc":
                    net.load_running_config()
                case "vtrt":
                    net.load_vtyshrt()
                case "vtyshrt":
                    net.load_vtyshrt()
                case "brctl":
                    net.load_brctl_show()
                case "a":
                    net.load_running_config()
                    net.load_vtyshrt()
                    net.load_brctl_show()
                case "all":
                    net.load_running_config()
                    net.load_vtyshrt()
                    net.load_brctl_show()
                case "q":
                    return
                case "quit":
                    return
                case _:
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
