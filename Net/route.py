from functools import reduce
import os
import pandas as pd
from colorama import Fore, Back, Style

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from binmanipulation import *
from .ip import get_net_ip, get_broadcast, ip_to_int, int_to_ip

BOLD = "\033[1m"


class RouteTable:
    def __init__(self):
        self.table = pd.DataFrame(
            columns=[
                "Type",
                "Destination",
                "Mask",
                "Cost",
                "NextHop",
                "Interface",
                "Selected",
                "MyCost",
                "Configured",
            ]
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Mask": "int",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        )

    def reset_routes(self):
        self.table = pd.DataFrame(
            columns=[
                "Type",
                "Destination",
                "Mask",
                "Cost",
                "NextHop",
                "Interface",
                "Selected",
                "MyCost",
                "Configured",
            ]
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Mask": "int",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Selected": "bool",
                "MyCost": "int",
                "Configured": "bool",
            }
        )
        return self.table

    def add_route(self, route) -> bool:
        # pprint(route)
        update = False
        if route["Destination"] in self.table["Destination"].values:
            for idx, row in self.table.query(
                "Destination == '{}'".format(route["Destination"])
            ).iterrows():
                if route["Type"] == row["Type"]:
                    if route["MyCost"] > row["MyCost"]:
                        break
                    # elif (
                    #     route["Interface"] != row["Interface"]
                    #     and route["Mask"] == row["Mask"]
                    #     and (route["Type"] == "C" or route["Type"] == "S")
                    # ):
                    #     raise Exception("Duplicate route with same interface and mask")
                    elif route["Mask"] == row["Mask"]:
                        break
                if route["Type"] == "S" and row["Type"] == "C":
                    if route["Mask"] == row["Mask"]:
                        break
            else:
                self.table = pd.concat(
                    [
                        self.table,
                        pd.DataFrame([route]).astype(
                            {
                                "Type": "string",
                                "Destination": "string",
                                "Mask": "int",
                                "Cost": "string",
                                "NextHop": "string",
                                "Interface": "string",
                                "Selected": "bool",
                                "MyCost": "int",
                                "Configured": "bool",
                            }
                        ),
                    ]
                )
                update = True
        else:
            self.table = pd.concat(
                [
                    self.table,
                    pd.DataFrame([route]).astype(
                        {
                            "Type": "string",
                            "Destination": "string",
                            "Mask": "int",
                            "Cost": "string",
                            "NextHop": "string",
                            "Interface": "string",
                            "Selected": "bool",
                            "MyCost": "int",
                        }
                    ),
                ]
            )
            update = True

        self.table = self.table.drop_duplicates()
        self.table = (
            self.table.assign(intip=self.table["Destination"].apply(ip_to_int))
            .sort_values(
                by=["intip", "Mask"], ascending=[True, False], ignore_index=True
            )
            .drop(columns=["intip"])
        )
        self.table = self.table.reset_index(drop=True)
        return update

    @staticmethod
    def split_rows(row):
        data = row.replace("  ", " ").replace("  ", " ").split(" ")
        Code = data[0].strip()
        network = data[1].strip()
        mask = None
        if network == "*":
            Code = "*"
            network = '" " "'
        else:
            if "/" in network:
                network, mask = network.split("/")
                mask = int(mask)
        i = 2
        connected = False
        cost = "x"
        if "[" in row:
            cost = data[2].strip()
            i = 3
        data2 = " ".join(data[i:]).split(",")
        via = (
            data2[0]
            .replace("via ", "")
            .replace("is directly connected", "direct connect")
            .strip()
        )
        interface = data2[1].strip()
        age = "x"
        if ":" in row:
            age = data2[2].strip()

        return {
            "Type": Code[0],
            "Destination": network,
            "Cost": cost,
            "NextHop": via,
            "Interface": interface,
            "Mask": mask,
            "Selected": True if ">" in Code else False,
            "MyCost": int(cost) if cost.isdigit() else 0,
            "Configured": True,
        }

    def loads_vtysh_routes(self, data):
        guide = "\n".join(data.splitlines()[:3])
        rows = data.splitlines()[4:]
        table = [RouteTable.split_rows(row) for row in rows]
        for n, row in enumerate(table):
            if row["Type"] == "*":
                row["Type"] = table[n - 1]["Type"]
                row["Destination"] = table[n - 1]["Destination"]
                row["Mask"] = table[n - 1]["Mask"]
        self.reset_routes()
        for route in table:
            self.add_route(route)

    @staticmethod
    def format_code(code, p):
        colors = {
            "O": Fore.YELLOW,
            "C": Fore.CYAN,
            "R": Fore.MAGENTA,
            "K": Fore.WHITE,
            "S": Fore.LIGHTBLACK_EX,
            "I": Fore.LIGHTWHITE_EX,
            "B": Fore.LIGHTRED_EX,
            "*": Fore.WHITE,
            ">": Fore.LIGHTMAGENTA_EX,
        }
        res = ""
        l = p
        if ">" in code:
            res += Back.LIGHTBLACK_EX + BOLD
            l += len(Back.LIGHTBLACK_EX + BOLD)
        for c in code:
            res += colors[c] + c
            l += len(colors[c])
        return (res + Style.RESET_ALL).center(l + len(Style.RESET_ALL))

    def format_table(self):
        table = Table(title="Routes")
        table.add_column("T", justify="center", style="cyan", no_wrap=True)
        table.add_column("Dest", justify="center", style="cyan", no_wrap=True)
        table.add_column("Mask", justify="center", style="cyan", no_wrap=True)
        table.add_column("Cost", justify="center", style="cyan", no_wrap=True)
        table.add_column("NextHop", justify="center", style="cyan", no_wrap=True)
        table.add_column("Iface", justify="center", style="cyan", no_wrap=True)
        # table.add_column("Sel", justify="center", style="cyan", no_wrap=True)
        # table.add_column("MyCost", justify="center", style="cyan", no_wrap=True)
        # table.add_column("Configured", justify="center", style="cyan", no_wrap=True)
        for _, row in self.table.iterrows():
            table.add_row(
                row["Type"],
                row["Destination"],
                str(row["Mask"]),
                row["Cost"],
                row["NextHop"].replace("direct connect", "direct"),
                row["Interface"],
                # str(row["Selected"]),
                # str(row["MyCost"]),
                # str(row["Configured"]),
                # green if selected else white
                style="green" if row["Selected"] else "white",
            )
        return table

    def __repr__(self) -> str:
        return self.format_table()

    def get_nexthop(self, ip):
        if "/" in ip:
            ip = ip.split("/")[0]
        for idx, row in self.table.iterrows():
            if row["Destination"] == get_net_ip(ip, row["Mask"]):
                return row["NextHop"]
        return None

    @staticmethod
    def compress_net_group(x, y):

        if type(x) != list:
            x = [x]
        # pprint(x)
        # pprint(y)
        # print("----")
        last = x[-1]

        if last["Interface"] != y["Interface"]:
            raise ValueError("NextHop mismatch")
        if last["Interface"] != y["Interface"]:
            raise ValueError("Interface mismatch")
        if last["Mask"] == y["Mask"]:
            if ip_to_int(
                get_broadcast(last["Destination"], last["Mask"])
            ) + 1 == ip_to_int(y["Destination"]):
                if x[-1]["Type"] == "C":
                    x[-1]["NextHop"] = y["NextHop"]
                x[-1]["Type"] = "S"
                x[-1]["Mask"] -= 1
                x[-1]["MyCost"] = min(last["MyCost"], y["MyCost"])
                x[-1]["Configured"] = False

                return reduce(RouteTable.compress_net_group, x)
            else:
                x.append(y)
                return x
        else:
            x.append(y)
        return x

    def merge_static_by_supernet(self):
        # filter out static routes
        static = (
            self.table.query("Type == 'S' or Type=='C'")
            .copy(deep=True)
            .sort_values(by=["Destination", "Mask"], ascending=[True, False])
        )
        # drop the static routes
        self.table = self.table.query("Type != 'S'")
        # group by next hop
        groups = static.groupby("Interface")
        # iterate over groups
        # print(self.format_table())
        for iface, group in groups:

            # compress the group to the minimum number of routes
            routes = reduce(
                RouteTable.compress_net_group,
                group.assign(intip=group["Destination"].apply(ip_to_int))
                .sort_values(
                    by=["intip", "Mask"], ascending=[True, False], ignore_index=True
                )
                .drop(columns=["intip"])
                .to_dict(orient="records"),
            )
            # pprint(routes)
            if type(routes) != list:
                routes = [routes]
            # print(pd.DataFrame(routes))
            # console=Console()
            # console.print(routes)
            # add the supernet to the table
            for route in routes:
                self.add_route(route)
        self.table = self.table.sort_values(
            by=["Destination", "Mask"], ascending=[True, False]
        )
        # static = (
        #     self.table.query("Type == 'S' or Type=='C'")
        #     .copy(deep=True)
        #     .sort_values(by=["Destination", "Mask"], ascending=[True, False])
        # )
        # self.table = self.table.query("Type != 'S'")

        # for idx, row in static.iterrows():
        #     if idx == len(static) - 1:
        #         continue
        #     if (
        #         row["Interface"] == static.iloc[idx + 1]["Interface"]
        #         and ip_to_int(get_broadcast(row["Destination"], row["Mask"])) + 1
        #         == ip_to_int(static.iloc[idx + 1]["Destination"])
        #         and get_net_ip(
        #             row["Destination"],
        #             max(row["Mask"], static.iloc[idx + 1]["Mask"]) - 1,
        #         )
        #         == get_net_ip(
        #             static.iloc[idx + 1]["Destination"],
        #             max(row["Mask"], static.iloc[idx + 1]["Mask"]) - 1,
        #         )
        #     ):

        #         if row["Type"] == "C":
        #             row["NextHop"] = static.iloc[idx + 1]["NextHop"]
        #         row["Type"] = "S"
        #         row["Mask"] -= 1
        #         row["MyCost"] = min(row["MyCost"], static.iloc[idx + 1]["MyCost"])
        #         row["Configured"] = False
        #         row["Destination"] = get_net_ip(
        #             row["Destination"],
        #             max(row["Mask"], static.iloc[idx + 1]["Mask"]) - 1,
        #         )
        #         self.add_route(row)

    def generate_static_routing_commands(self, router=None):
        commands = []
        for idx, row in self.table.query("Type == 'S'").iterrows():
            command = f"ip route add {row['Destination']}/{row['Mask']} via {row['NextHop'].split('/')[0]} dev {row['Interface']}"
            if row["Configured"]:
                continue
            if router is None:
                commands.append(command)
            else:
                commands.append(f"lxc-attach -n {router} -- {command}")
        return commands

    def apply_static_routes(self, router=None):
        commands = self.generate_static_routing_commands(router)
        for command in commands:
            print(command)
            os.system(command)

    def check_table(self):
        # goup by destination and mask
        groups = self.table.groupby(["Destination", "Mask"])
        # iterate over groups
        for (dest, mask), group in groups:
            # if there are more than one route
            if len(group) > 1:
                # get the first route
                first = group.iloc[0]
                # iterate over the group
                for idx, row in group.iterrows():
                    # if the route is not the same as the first and has a different interface
                    if (
                        not (first == row).all()
                        and first["Interface"] != row["Interface"]
                    ):
                        # print the group
                        print(group)
                        # raise an exception
                        raise Exception("Duplicate route")
