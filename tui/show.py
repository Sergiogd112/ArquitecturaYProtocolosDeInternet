from subprocess import run
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.columns import Columns
from rich.syntax import Syntax
from rich.pretty import Pretty
from rich.tree import Tree

import pandas as pd
from Net import Net
from Net.ip import get_net_ip


class Show:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()

    def show_scenario(self, net: Net):
        while True:
            self.console.print("Show scenario")
            self.console.print("What do you want to show?")
            commands = [
                ["n", "net"],
                ["r", "routers"],
                ["b", "briges"],
                ["brctl"],
                ["rt", "routes"],
                ["vrc", "vtyshrc"],
                ["vrt", "vtyshrt"],
                ["o", "ospf"],
                ["p", "pimd"],
                ["m", "mroute"],
                ["bgp"],
                ["bgps", "bgp summary"],
                ["q", "quit"],
            ]
            table = Table(
                show_header=True,
                header_style="bold magenta",
                title="Commands",
                show_lines=True,
            )
            table.add_column("Short command")
            table.add_column("Command")
            for cmd in commands:
                if len(cmd) == 2:
                    table.add_row(cmd[0], cmd[1])
                else:
                    table.add_row("", cmd[0])
            self.console.print(table, justify="center")
            opt = Prompt.ask(
                "Select an option",
                choices=[cmd for row in commands for cmd in row],
                show_choices=False,
            )
            if opt == "n" or opt == "net":
                self.show_net(net)
            elif opt == "r" or opt == "routers":
                self.show_routers(net)
            elif opt == "b" or opt == "bridges":
                self.show_bridges(net)
            elif opt == "brctl":
                self.show_brctl()
            elif opt == "rt":
                self.show_routes(net)
            elif opt == "vrc":
                self.show_vtyshrc(net)
            elif opt == "vrt":
                self.show_vtyshrt(net)
            elif opt == "o" or opt == "ospf":
                self.show_ospf(net)
            elif opt == "p" or opt == "pimd":
                self.show_pimd_conf(net)
            elif opt == "m" or opt == "mroute":
                self.show_mroute(net)
            elif opt == "bgp":
                self.show_bgp(net)
            elif opt == "bgps" or opt == "bgp summary":
                self.show_bgp_summary(net)
            elif opt == "q":
                return

    def show_net(self, net: Net):
        self.console.print("Show net")
        self.console.print(Panel(Pretty(net.routers), title="Routers"))
        self.console.print(Panel(Pretty(net.bridges), title="Bridges"))

    @staticmethod
    def dict_to_md(data: dict) -> str:
        # generate markdown list from a dictionary
        # recursive function
        md = ""
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                md += f"- {key}:\n"
                md += "  " + Show.dict_to_md(value).replace("\n", "\n  ")
            elif isinstance(value, list):
                md += f"- {key}:\n"
                md += "  " + Show.list_to_md(value).replace("\n", "\n  ")
            else:
                md += f"- {key}: {value}\n"
        return md

    @staticmethod
    def list_to_md(data: list) -> str:
        # generate markdown list from a list
        # recursive function
        md = ""
        for n, item in enumerate(data):
            if isinstance(item, dict):
                md += f"- {n}:\n"
                md += "  " + Show.dict_to_md(item).replace("\n", "\n  ")
            elif isinstance(item, list):
                md += f"- {n}:\n"
                md += "  " + Show.list_to_md(item).replace("\n", "\n  ")
            else:
                md += f"- {n}: {item}\n"
        return md

    def dict_to_tree(self, data: dict, name: str) -> Tree:
        tree = Tree(name)
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                subtree = self.dict_to_tree(value, key)
                tree.add(subtree)
            elif isinstance(value, list):
                subtree = self.list_to_tree(value, key)
                tree.add(subtree)
            else:
                tree.add(key + ": " + str(value))
        return tree

    def list_to_tree(self, data: list, name: str) -> Tree:
        tree = Tree(name)
        for n, item in enumerate(data):
            if isinstance(item, dict):
                subtree = self.dict_to_tree(item, str(n))
                tree.add(subtree)
            elif isinstance(item, list):
                subtree = self.list_to_tree(item, str(n))
                tree.add(subtree)
            else:
                tree.add(str(n) + ": " + str(item))
        return tree

    def show_router(self, router: str, conf: dict, printout: bool = False) -> Panel:
        tables = []
        for sect, block in conf.items():
            # self.console.print(sect)
            # self.console.print(block)
            # self.console.print(block)
            # Prompt.ask("Press enter to continue")

            if "bgp" in sect:
                tables += [Panel(self.dict_to_tree(block, "bgp"), title=sect)]
                continue
            df = pd.DataFrame(block).T
            if "ospf" in sect:
                df = df.T
            tables += [Table(show_header=True, title=sect, header_style="bold magenta")]
            tables[-1].add_column("Key")
            for col in df.columns:
                tables[-1].add_column(col)

            for idx, row in df.iterrows():
                tables[-1].add_row(*([str(idx)] + [repr(val) for val in row.values]))

            # self.console.print(tables[-1])
        if printout:
            self.console.print(
                Panel(
                    Group(*tables, fit=True),
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        return Panel(
            Group(*tables, fit=True),
            title="[bold magenta]" + router + "[/bold magenta]",
        )

    def show_routers(self, net: Net):
        self.console.print("Show routers")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            conf = net.routers[router]
            panel = self.show_router(router, conf, printout=False)
            columns.add_renderable(panel)
        self.console.print(columns)

    def show_bridge(self, bridge: str, conf: dict, printout=False):
        text = ""
        for key, value in conf.items():
            if type(value) is list:
                text += f"- {key}:\n"
                for i in value:
                    text += f"  - {i}\n"
            else:
                text += f"- {key}: {value}\n"
        panel = Panel(text, title="[bold magenta]" + bridge + "[/bold magenta]")
        if printout:
            self.console.print(panel)
        return panel

    def show_bridges(self, net):
        self.console.print("Show bridges")
        columns = Columns(expand=True)
        # self.console.print(net.netdict)
        if len(net.bridges) < 1:
            self.console.print("No bridges found")
            return
        for bridge in sorted(list(net.bridges.keys())):
            conf = net.bridges[bridge]
            panel = self.show_bridge(bridge, conf)
            columns.add_renderable(panel)
        self.console.print(columns)

    def show_brctl(self):
        self.console.print("Show brctl")
        table = Table(show_header=True, header_style="bold magenta")
        consoleout = run(
            ["brctl", "show"],
            capture_output=True,
            text=True,
        ).stdout

        lines = consoleout.split("\n")
        headers = [head for head in lines[0].split("\t") if head != ""]
        for header in headers:
            table.add_column(header.strip())
        for line in lines[1:]:
            if line == "":
                continue
            row = [cell.strip() for cell in line.split("\t") if cell != ""]
            if "lxc" in row[0]:
                row += [""] * (len(headers) - len(row))
            if len(row) < len(headers) and "br" not in row[0]:
                row = [""] * (len(headers) - len(row)) + row
            elif len(row) < len(headers) and "br" in row[0]:
                row = row + [""] * (len(headers) - len(row))

            table.add_row(*row)
        self.console.print(table)

    def show_routes(self, net: Net):
        self.console.print("Show routes")
        columns = Columns(expand=True, align="center")
        for router in sorted(net.routes.keys()):
            routes = net.routes[router]
            self.console.print(router)
            columns.add_renderable(
                Panel(
                    routes.format_table(),
                    title=router,
                    style="bold " + ("magenta" if "R" in router else "blue"),
                )
            )
        self.console.print(columns)

    def show_vtyshrc(self, net: Net):
        self.console.print("Show vtyshrc")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                ["lxc-attach", "-n", router, "--", "vtysh", "-c", "show running"],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_vtyshrt(self, net: Net):
        self.console.print("Show vtyshrt")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                ["lxc-attach", "-n", router, "--", "vtysh", "-c", "show ip route"],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_ospf(self, net: Net):
        self.console.print("Show ospf")
        while True:
            opt = Prompt.ask(
                "Select an option",
                choices=["r", "router", "n", "network", "s", "summary", "q", "quit"],
            )
            if opt == "r" or opt == "router":
                self.show_ospf_routers(net)
            elif opt == "n" or opt == "network":
                self.show_ospf_networks(net)
            elif opt == "s" or opt == "summary":
                self.show_ospf_summarys(net)
            elif opt == "q" or opt == "quit":
                return

    def show_ospf_router(self, net: Net, router, area):
        consoleout = run(
            [
                "lxc-attach",
                "-n",
                router,
                "--",
                "vtysh",
                "-c",
                "show ip ospf database router",
            ],
            capture_output=True,
            text=True,
            # check=True,
        ).stdout
        arealsarr = consoleout.split("Router Link States (Area ")
        columns = Columns(expand=True)
        df = pd.DataFrame(columns=["Advertising Router", "Router name"])
        for areals in arealsarr[1:]:
            areaid = areals.split(")")[0]
            if areaid == area:
                content = ")\n".join(areals.split(")\n")[1:]).strip()
                for ls in content.split("\n\n\n"):
                    advertising_router = ls.split("Advertising Router: ")[1].split(
                        "\n"
                    )[0]
                    rname = net.get_router_with_ip(advertising_router)
                    df = pd.concat(
                        [
                            df,
                            pd.DataFrame(
                                [[advertising_router, rname]], columns=df.columns
                            ),
                        ],
                        ignore_index=True,
                    )
                    columns.add_renderable(
                        Panel(
                            ls,
                            title="[bold magenta]"
                            + advertising_router
                            + "|"
                            + rname
                            + "[/bold magenta]",
                        )
                    )
                break
        table = Table(show_header=True, header_style="bold magenta")
        df = df.sort_values(by="Router name")
        for col in df.columns:
            table.add_column(col)
        for _, row in df.iterrows():
            table.add_row(*[val for val in row.values])
        columns.add_renderable(table)
        return Panel(
            columns,
            title="[bold magenta]" + area + "[/bold magenta]",
        )

    def show_ospf_routers(self, net: Net):
        self.console.print("Show ospf router")
        columns = Columns(expand=True)
        areas = net.get_ospf_areas()
        for area in sorted(list(areas.keys())):
            router = areas[area][0]

            columns.add_renderable(self.show_ospf_router(net, router, area))
        self.console.print(columns)

    def show_ospf_network(self, net: Net, router, area):
        consoleout = run(
            [
                "lxc-attach",
                "-n",
                router,
                "--",
                "vtysh",
                "-c",
                "show ip ospf database network",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        arealsarr = consoleout.split("Net Link States (Area ")
        columns = Columns(expand=True)
        df = pd.DataFrame(columns=["Link ID", "Advertising Router", "Router name"])
        for areals in arealsarr[1:]:
            areaid = areals.split(")")[0]
            if areaid == area:
                content = ")\n".join(areals.split(")\n")[1:]).strip()
                for ls in content.split("\n\n"):
                    linkid = ls.split("Link State ID: ")[1].strip().split(" ")[0]
                    mask = ls.split("Network Mask: ")[1].strip().split("\n")[0]
                    netip = get_net_ip(linkid + mask)
                    brg = net.get_brg_with_netip(netip)
                    advertising_router = ls.split("Advertising Router: ")[1].split(
                        "\n"
                    )[0]
                    routername = net.get_router_with_ip(advertising_router)
                    df = pd.concat(
                        [
                            df,
                            pd.DataFrame(
                                [[linkid, advertising_router, routername]],
                                columns=df.columns,
                            ),
                        ],
                        ignore_index=True,
                    )
                    columns.add_renderable(
                        Panel(
                            ls,
                            title="[bold magenta]"
                            + netip
                            + mask
                            + "|"
                            + brg
                            + "[/bold magenta]",
                        )
                    )
                break
        table = Table(show_header=True, header_style="bold magenta")
        df = df.sort_values(by="Router name")
        for col in df.columns:
            table.add_column(col)
        for _, row in df.iterrows():
            table.add_row(*[val for val in row.values])
        columns.add_renderable(table)
        return Panel(
            columns,
            title="[bold magenta]" + area + "[/bold magenta]",
        )

    def show_ospf_networks(self, net: Net):
        self.console.print("Show ospf network")
        columns = Columns(expand=True)
        areas = net.get_ospf_areas()
        for area in sorted(list(areas.keys())):
            router = areas[area][0]
            columns.add_renderable(self.show_ospf_network(net, router, area))
        self.console.print(columns)

    def show_ospf_summarys(self, net: Net):
        self.console.print("Show ospf summary")
        columns = Columns(expand=True)
        areas = net.get_ospf_areas()
        for area in sorted(list(areas.keys())):
            router = areas[area][0]
            consoleout = run(
                [
                    "lxc-attach",
                    "-n",
                    router,
                    "--",
                    "vtysh",
                    "-c",
                    "show ip ospf database summary",
                ],
                capture_output=True,
                text=True,
                # check=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + area + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_pimd_conf(self, net: Net):
        self.console.print("Show pimd conf")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                ["lxc-attach", "-n", router, "--", "cat", "/root/pimd/pimd.conf"],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    Syntax(consoleout, "conf", line_numbers=True),
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_mroute(self, net: Net):
        self.console.print("Show mroute")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                ["lxc-attach", "-n", router, "--", "mroute"],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_bgp(self, net: Net):
        self.console.print("Show bgp")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                ["lxc-attach", "-n", router, "--", "vtysh", "-c", "show ip bgp"],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)

    def show_bgp_summary(self, net: Net):
        self.console.print("Show bgp summary")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            consoleout = run(
                [
                    "lxc-attach",
                    "-n",
                    router,
                    "--",
                    "vtysh",
                    "-c",
                    "show ip bgp summary",
                ],
                capture_output=True,
                text=True,
            ).stdout
            columns.add_renderable(
                Panel(
                    consoleout,
                    title="[bold magenta]" + router + "[/bold magenta]",
                )
            )
        self.console.print(columns)
