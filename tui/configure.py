from subprocess import run
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.columns import Columns
import pandas as pd
from show import Show


class Configure:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()

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
            iface = Prompt.ask(
                "Select an iface",
                choices=["q", "quit"] + net.routers[router]["iface"].keys(),
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

    def configure_solver(self, stype):
        self.console.print("Configure scenario")
        stype = Prompt.ask("Select the type", choices=["static", "rip", "ospf", "bgp"])
        self.console.print("Selected type: " + stype)

        return stype
