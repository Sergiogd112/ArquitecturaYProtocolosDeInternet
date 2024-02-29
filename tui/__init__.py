from subprocess import run
from rich.console import Console, Group
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

from .show import Show
from .configure import Configure


class TUI:
    def __init__(self) -> None:
        self.console = Console()
        self.layout = Layout()
        self.stype = ""
        self.net = None
        self.show = Show()
        self.configure = None

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
        ppath = os.path.join("/home", "api", "practiques")
        if not os.path.exists(ppath):
            ppath = os.path.join("practiques")
        practs = [
            path[1:]
            for path in os.listdir(ppath)
            if os.path.isdir(os.path.join(ppath, path)) and "P" in path
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
                scenario
                for scenario in os.listdir(os.path.join(ppath, pract))
                if os.path.isdir(os.path.join(ppath, pract, scenario))
                and "E" in scenario
                and "backup" not in scenario
            ]

            scneario = (
                scenarios[0].split("E")[0]
                + "E"
                + Prompt.ask(
                    "Select a scenario in {}".format(pract),
                    choices=[scneario.split("E")[1] for scneario in scenarios],
                )
            )
            if "A" in pract:
                self.scenario_state(scneario,pract)
            else:
                self.scenario_state(scneario,pract="")

    def scenario_state(self, scenario,pract):
        self.net = Net.read_scenario(scenario,pract)
        self.configure = Configure(scenario)
        self.show.show_routers(self.net)
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
                ["st", "stop", "Stop the scenario"],
                ["ru", "run", "Run the scenario"],
                ["r", "restart", "Restart the scenario"],
                ["rr", "restart-run", "Restart and run the scenario"],
                ["c", "configure", "Configure the scenario and solver type"],
                ["l", "load", "Load the current configuration"],
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
            if option == "s":
                self.start_scenario(scenario)
            elif option == "r":
                self.restart_scenario(scenario)
            elif option == "st":
                self.stop_scenario(scenario)
            elif option == "ru":
                self.run_scenario(scenario)
            elif option == "rr":
                self.restart_run_scenario(scenario)
            elif option == "c":
                self.configure.run(self.net, self.stype)
            elif option == "l":
                self.configure.load_scenario(self.net)
            elif option == "sh":
                self.show.show_scenario(self.net)
            elif option == "t":
                self.check_scenario()
            elif option == "q":
                return
            else:
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
        if self.net is None:
            self.net = Net.read_scenario(scenario)
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
            idx = Prompt.ask(
                "Select a start script",
                choices=[str(i) for i in range(len(starts))] + ["quit", "q"],
            )
            if idx == "quit" or idx == "q":
                return
            idx = int(idx)
            self.console.print("Selected: " + starts[idx])
            os.system(starts[idx])
            self.net.read_scenario_subconfigs(scenario, starts[idx].split("-")[-1])
            self.show.show_routers(self.net)
            self.show.show_bridges(self.net)
            self.show.show_routes(self.net)

    def stop_scenario(self, scenario):
        self.console.print("Stopping scenario: " + scenario)
        os.system(f"{scenario}-stop")
        self.net = None

    def restart_scenario(self, scenario):
        self.console.print("Restarting scenario: " + scenario)
        self.stop_scenario(scenario)
        self.start_scenario(scenario)

    def run_scenario(self, scenario):
        self.console.print("Running scenario: " + scenario)
        if self.stype == "":
            self.console.print("Solver type not selected")
            self.configure_scenario()
        if self.stype == "static":
            self.run_static(scenario)
        elif self.stype == "rip":
            self.run_rip(scenario)
        elif self.stype == "ospf":
            self.run_ospf(scenario)
        elif self.stype == "bgp":
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
        opt=Prompt.ask("Generate non direct routes?",choices=["y","n"],default="n")
        if opt=="y":
            self.net.generate_non_direct_routes()
        self.net.check_routes()
        self.net.apply_configuration()
        self.console.print("Static configuration applied")
        if Prompt.ask("Test the configuration?", choices=["y", "n"]) == "y":
            self.check_scenario()

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
        for row in self.net.bridges_to_list():
            table.add_row(*[cell.__repr__() for cell in row])
        self.console.print(table)
        opt = Prompt.ask(
            "Select a network to modify",
            choices=[row[0] for row in self.net.bridges_to_list()],
        )
        self.console.print("Selected: " + opt)
        # ask for the ammount of devices (larger than 2 or the current amount of devices)

        while True:
            amount = Prompt.ask(
                "Amount of devices",
                default=self.net.bridges[opt]["devcount"],
            )
            try:
                amount = int(amount)
                break
            except ValueError:
                self.console.print("Invalid input. Please enter a valid integer.")

        self.net.bridges[opt]["devcount"] = amount
        if Prompt.ask("Modify another network?", choices=["y", "n"]) == "y":
            self.modify_devcount(scenario)

    def run_rip(self, scenario):
        self.console.print("TODO: RIP configuration")

    def run_ospf(self, scenario):
        
        self.console.print("TODO: OSPF configuration")

    def run_bgp(self, scenario):
        self.console.print("TODO: BGP configuration")
        

    def check_scenario(self):
        working, total = self.net.check_all_connections(True)
        if working == total:
            panel = Panel(
                Text(
                    f"Working: {working} Total: {total} percentage: {working / total * 100:.2f}% :check-mark:",
                    justify="center",
                ),
                style="bold green",
                title="Test result",
            )
        else:
            panel = Panel(
                Text(
                    f"Working: {working} Total: {total} percentage: {working / total * 100:.2f}%:cross_mark:",
                    justify="center",
                ),
                style="bold red",
                title="Test result",
            )
        self.console.print(panel)


if __name__ == "__main__":
    tui = TUI()
    tui.lobby()
