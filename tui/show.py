from subprocess import run
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.columns import Columns
import pandas as pd
from net import Net


class Show:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()

    def show_scenario(self, net):
        while True:
            self.console.print("Show scenario")
            self.console.print("What do you want to show?")
            opt = Prompt.ask(
                "Select an option",
                choices=[
                    "r",
                    "routers",
                    "b",
                    "briges",
                    "brctl",
                    "rt",
                    "routes",
                    "vrc",
                    "vtyshrc",
                    "vrt",
                    "vtyshrt",
                    "q",
                    "quit",
                ],
            )
            match opt:
                case "r":
                    self.show_routers(net)
                case "routers":
                    self.show_routers(net)
                case "b":
                    self.show_bridges(net)
                case "bridges":
                    self.show_bridges(net)
                case "brctl":
                    self.show_brctl(net)
                case "rt":
                    self.show_routes(net)
                case "vrc":
                    self.show_vtyshrc(net)
                case "vrt":
                    self.show_vtyshrt(net)
                case "q":
                    return

    def show_router(
        self, net: "Net", router: str, conf: dict, printout: bool = False
    ) -> Panel:
        tables = []
        for sect, block in conf.items():
            # self.console.print(sect)
            # self.console.print(block)

            df = pd.DataFrame(block).T
            if "ospf" in sect:
                df = df.T
            tables += [Table(show_header=True, title=sect, header_style="bold magenta")]
            tables[-1].add_column("Key")
            for col in df.columns:
                tables[-1].add_column(col)

            for idx, row in df.iterrows():
                tables[-1].add_row(
                    *([str(idx)] + [val.__repr__() for val in row.values])
                )
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

    def show_routers(self, net):
        self.console.print("Show routers")
        columns = Columns(expand=True)
        for router in sorted(list(net.routers.keys())):
            conf = net.routers[router]
            panel = self.show_router(net, router, conf, printout=False)
            columns.add_renderable(panel)
        self.console.print(columns)

    def show_bridge(self, bridge, conf, printout=False):
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

    def show_brctl(self, net):
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

    def show_routes(self, net):
        self.console.print("Show routes")
        columns = Columns(expand=True)
        for router, routes in net.routes.items():
            self.console.print(router)
            columns.add_renderable(Panel(routes.format_table(), title=router))
        self.console.print(columns)

    def show_vtyshrc(self, net):
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

    def show_vtyshrt(self, net):
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
