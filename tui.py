from re import sub
from subprocess import run
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.layout import Layout

# from rich.live import Live
from rich.pretty import Pretty

from rich.columns import Columns
import pandas as pd
import os

from net import Net


class TUI:
    def __init__(self) -> None:
        self.console = Console()
        self.layout = Layout()
        self.stype = ""
        self.net = None

    def lobby(self):
        self.net = None
        self.console.print(
            Panel(
                Text("Welcome to the API solver", justify="center"),
                title="TUI",
                style="bold green",
                border_style="green",
            )
        )
        practs = [
            path[1:]
            for path in os.listdir(os.path.join("/home", "api", "practiques"))
            if os.path.isdir(os.path.join("/home", "api", "practiques", path))
            and "P" in path
        ]
        while True:
            pract = Prompt.ask(
                "Select a practice",
                choices=practs + ["q", "quit"],
            )
            if pract == "quit" or pract == "q":
                exit()
            pract = "P" + pract
            scenarios = [
                scenario.split("-")[1]
                for scenario in os.listdir(
                    os.path.join("/home", "api", "practiques", pract)
                )
                if os.path.isdir(
                    os.path.join("/home", "api", "practiques", pract, scenario)
                )
                and "E" in scenario
                and "backup" not in scenario
            ]
            scneario = (
                pract
                + "-E"
                + Prompt.ask(
                    "Select a scenario in {}".format(pract),
                    choices=[scneario.split("E")[1] for scneario in scenarios],
                )
            )
            self.scenario_state(scneario)

    def scenario_state(self, scenario):
        self.net = Net.read_scenario(scenario)
        self.show_routers()
        while True:
            self.console.print(
                "Scenario: " + scenario + "Type: " + self.stype, style="bold green"
            )
            table = Table(
                title="Options",
                show_lines=True,
                show_header=True,
                header_style="bold",
                border_style="green",
            )
            tablearr = [
                ["s", "start", "Start the scenario"],
                ["r", "restart", "Restart the scenario"],
                ["st", "stop", "Stop the scenario"],
                ["ru", "run", "Run the scenario"],
                ["rr", "restart-run", "Restart and run the scenario"],
                ["c", "configure", "Configure the solver"],
                ["sh", "show", "Show the current configuration"],
                ["t", "test", "Test the current configuration"],
                ["q", "quit", "Quit the scenario"],
            ]
            table.add_column("short", justify="center", style="bold green")
            table.add_column("long", justify="center", style="bold magenta")
            table.add_column("description", justify="center")
            for row in tablearr:
                table.add_row(*row)
            # panel = Panel(table, title="Scenario: " + scenario, style="bold green")
            self.console.print(table, justify="center")

            option = Prompt.ask(">>>", choices=[row[0] for row in tablearr])
            print(option)
            match option:
                case "s":
                    self.start_scenario(scenario)
                case "r":
                    self.restart_scenario(scenario)
                case "st":
                    self.stop_scenario(scenario)
                case "ru":
                    self.run_scenario(scenario)
                case "rr":
                    self.restart_run_scenario(scenario)
                case "c":
                    self.configure_scenario()
                case "sh":
                    self.show_scenario()
                case "t":
                    self.check_scenario()
                case "q":
                    return
                case _:
                    self.console.print("Invalid option")

    def start_scenario(self, scenario):
        self.console.print("Starting scenario: " + scenario)
        starts = [
            script
            for script in os.listdir(os.path.join("/home", "api", "practiques"))
            if "start" in script and scenario in script
        ]
        if len(starts) < 1:
            self.console.print("No start script found")
            return
        if len(starts) == 1:
            os.system(starts[0])
        self.console.print("Select a start script")
        while True:
            table = Table(
                title="Start scripts",
                show_header=True,
                header_style="bold",
                border_style="green",
            )
            table.add_column("id", justify="center", style="bold green")
            table.add_column("script", justify="center")
            for i, script in enumerate(starts):
                table.add_row(str(i), script)
            self.console.print(table)
            id = Prompt.ask(
                "Select a start script",
                choices=[str(i) for i in range(len(starts))] + ["quit", "q"],
            )
            if id == "quit" or id == "q":
                return
            id = int(id)
            self.console.print("Selected: " + starts[id])
            os.system(starts[id])
            self.net.read_scenario_subconfigs(scenario, starts[id].split("-")[-1])

    def stop_scenario(self, scenario):
        self.console.print("Stopping scenario: " + scenario)
        os.system(f"{scenario}-stop")

    def restart_scenario(self, scenario):
        self.console.print("Restarting scenario: " + scenario)
        self.stop_scenario(scenario)
        self.start_scenario(scenario)

    def run_scenario(self, scenario):
        self.console.print("Running scenario: " + scenario)
        if self.stype == "":
            self.console.print("Solver type not selected")
            self.configure_scenario()
        match self.stype:
            case "static":
                self.run_static(scenario)
            case "rip":
                self.run_rip(scenario)
            case "ospf":
                self.run_ospf(scenario)
            case "bgp":
                self.run_bgp(scenario)

    def configure_scenario(self):
        self.console.print("Configure scenario")
        self.stype = Prompt.ask(
            "Select the type", choices=["static", "rip", "ospf", "bgp"]
        )
        self.console.print("Selected type: " + self.stype)

    def restart_run_scenario(self, scenario):
        self.restart_scenario(scenario)
        self.run_scenario(scenario)

    def run_static(self, scenario):
        self.console.print("Running static")
        while True:
            sel = Prompt.ask(
                "Modify the number of devices per network?",
                choices=["y", "n"],
                default="n",
            )
            if sel == "n":
                break
            self.modify_devcount(scenario)
        iprange = Prompt.ask("IP range:", default="10.0.0.0/24")
        self.net.assign_subnets(iprange)
        _, commands = self.net.assign_ips(True)
        for command in commands:
            os.system(command)
        self.net.generate_routes()
        self.net.generate_non_direct_routes()
        self.net.check_routes()
        self.net.apply_configuration()
        self.console.print("Static configuration applied")
        if Prompt.ask("Test the configuration?", choices=["y", "n"]) == "y":
            working, total = self.net.check_all_connections(True)
            if working == total:
                panel = Panel(
                    Text(
                        f"Working: {working} Total: {total} percentage: {working/total*100:.2f}%:check-mark:",
                        justify="center",
                    ),
                    style="bold green",
                    title="Test result",
                )
            else:
                panel = Panel(
                    Text(
                        f"Working: {working} Total: {total} percentage: {working/total*100:.2f}%:cross_mark:",
                        justify="center",
                    ),
                    style="bold red",
                    title="Test result",
                )
            self.console.print(panel)

    def modify_devcount(self, scenario):
        self.console.print("Modify devcount")
        self.console.print(self.net.routers)
        table = Table(
            title="Networks",
            show_lines=True,
            show_header=True,
            header_style="bold",
            border_style="green",
        )
        table.add_column("Bridge", justify="center", style="bold green")
        table.add_column("Devcount", justify="center")
        table.add_column("Routers", justify="center")
        # self.console.print(self.net.netdict)
        # self.console.print(self.net.netdic_to_list())
        # self.console.print(self.net.netdic_to_list())
        for row in self.net.netdic_to_list():
            table.add_row(*[cell.__repr__() for cell in row])
        self.console.print(table)
        opt = Prompt.ask(
            "Select a network to modify",
            choices=[row[0] for row in self.net.netdic_to_list()],
        )
        self.console.print("Selected: " + opt)
        # ask for the ammount of devices (larger than 2 or the current amount of devices)

        while True:
            amount = Prompt.ask(
                "Amount of devices",
                default=self.net.netdict[opt]["devcount"],
            )
            try:
                amount = int(amount)
                break
            except ValueError:
                self.console.print("Invalid input. Please enter a valid integer.")

        self.net.netdict[opt]["devcount"] = amount
        if Prompt.ask("Modify another network?", choices=["y", "n"]) == "y":
            self.modify_devcount(scenario)

    def run_rip(self, scenario):
        pass

    def run_ospf(self, scenario):
        pass

    def run_bgp(self, scenario):
        pass

    def show_scenario(
        self,
    ):
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
                    self.show_routers()
                case "routers":
                    self.show_routers()
                case "b":
                    self.show_bridges()
                case "bridges":
                    self.show_bridges()
                case "brctl":
                    self.show_brctl()
                case "rt":
                    self.show_routes()
                case "vrc":
                    self.show_vtyshrc()
                case "vrt":
                    self.show_vtyshrt()
                case "q":
                    return

    def show_routers(
        self,
    ):
        self.console.print("Show routers")
        columns = Columns(expand=True)
        for router, conf in self.net.routers.items():
            self.console.print(router)
            self.console.print(conf)
            tables = []
            for sect, block in conf.items():
                tables += [
                    Table(show_header=True, title=sect, header_style="bold magenta")
                ]
                df = pd.DataFrame(block).T
                for col in df.columns:
                    tables[-1].add_column(col)
                for row in df.iterrows():
                    tables[-1].add_row(*row[1])

            columns.add_renderable(
                Panel(*tables, title="[bold magenta]" + router + "[/bold magenta]")
            )
        self.console.print(columns)

    def show_bridges(
        self,
    ):
        self.console.print("Show bridges")
        columns = Columns(expand=True)
        # self.console.print(self.net.netdict)
        if len(self.net.netdict) < 1:
            self.console.print("No bridges found")
            return
        for bridge, conf in self.net.netdict.items():
            text = ""
            for key, value in conf.items():
                if type(value) is list:
                    text += f"- {key}:\n"
                    for i in value:
                        text += f"  - {i}\n"
                else:
                    text += f"- {key}: {value}\n"
            panel = Panel(text, title="[bold magenta]" + bridge + "[/bold magenta]")

            columns.add_renderable(panel)
        self.console.print(columns)

    def show_brctl(
        self,
    ):
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
            if len(row) < len(headers):
                row = [""] * (len(headers) - len(row)) + row
            table.add_row(*row)
        self.console.print(table)

    def show_routes(
        self,
    ):
        self.console.print("Show routes")
        columns = Columns(expand=True)
        for router, routes in self.net.routes.items():

            columns.add_renderable(routes.format_table())
        self.console.print(columns)

    def show_vtyshrc(
        self,
    ):
        self.console.print("Show vtyshrc")
        columns = Columns(expand=True)
        for router, _ in self.net.routers.items():
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

    def show_vtyshrt(self):
        self.console.print("Show vtyshrt")
        columns = Columns(expand=True)
        for router, _ in self.net.routers.items():
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

    def check_scenario(self):
        self.net.check_all_connections(True)


if __name__ == "__main__":
    tui = TUI()
    tui.lobby()
