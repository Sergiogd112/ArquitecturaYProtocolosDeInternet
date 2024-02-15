from functools import reduce
from pprint import pprint
import pandas as pd
from colorama import Fore, Back, Style
from ip import get_net_ip, get_broadcast, ip_to_int, int_to_ip
from binmanipulation import *

BOLD = "\033[1m"


class RouteTable:
    def __init__(self):
        self.table = pd.DataFrame(
            columns=[
                "Type",
                "Destination",
                "Cost",
                "NextHop",
                "Interface",
                "Mask",
                "Selected",
                "MyCost",
                "Configured",
            ]
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
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
                "Cost",
                "NextHop",
                "Interface",
                "Mask",
                "Selected",
                "MyCost",
                "Configured",
            ]
        ).astype(
            {
                "Type": "string",
                "Destination": "string",
                "Cost": "string",
                "NextHop": "string",
                "Interface": "string",
                "Mask": "int",
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
                    elif (
                        route["Interface"] != row["Interface"]
                        and route["Mask"] == row["Mask"]
                        and (route["Type"] == "C" or route["Type"] == "S")
                    ):
                        raise Exception("Duplicate route with same interface and mask")
                    elif route["Mask"] == row["Mask"]:
                        break
                if route["Type"] == "S" and row["Type"] == "C":
                    break
            else:
                self.table = pd.concat(
                    [
                        self.table,
                        pd.DataFrame([route]).astype(
                            {
                                "Type": "string",
                                "Destination": "string",
                                "Cost": "string",
                                "NextHop": "string",
                                "Interface": "string",
                                "Mask": "int",
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
                            "Cost": "string",
                            "NextHop": "string",
                            "Interface": "string",
                            "Mask": "int",
                            "Selected": "bool",
                            "MyCost": "int",
                        }
                    ),
                ]
            )
            update = True

        self.table = self.table.drop_duplicates()
        self.table = self.table.sort_values(
            by=["Destination", "Mask"], ascending=[True, False]
        )
        self.table = self.table.reset_index(drop=True)
        return update

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
            "Configured": True if "C" in Code else False,
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
        clens = [
            max(col)
            for col in zip(*[[len(str(c)) for c in row] for row in self.table.values])
        ]
        headers = list(self.table.columns)
        lens = [max(a, len(b)) for a, b in zip(clens, headers)]
        separator = "+" + "+".join(["-" * (l + 2) for l in lens]) + "+"
        headerstr = (
            "|"
            + "|".join(
                [
                    " " + BOLD + str(header).center(l) + Style.RESET_ALL + " "
                    for header, l in zip(headers, lens)
                ]
            )
            + "|"
        )
        text = ""
        text += separator + "\n"
        text += (headerstr) + "\n"
        for n, row in self.table.iterrows():
            rowstr = "| " + RouteTable.format_code(row["Type"], lens[0]) + " "
            rowstr += (
                "|"
                + "|".join(
                    [
                        (
                            " "
                            + BOLD
                            + Back.LIGHTBLACK_EX
                            + str(c).center(l)
                            + Style.RESET_ALL
                            + " "
                            if row["Selected"]
                            else " " + str(c).center(l) + " "
                        )
                        for c, l in zip(
                            row[list(self.table.drop(columns=["Type"]).columns)],
                            lens[1:],
                        )
                    ]
                )
                + "|"
            )
            if not ('"' in row["Destination"]):
                text += separator + "\n"
            text += rowstr + "\n"
        text += separator
        return text

    def __repr__(self) -> str:
        return self.format_table()

    def get_nexthop(self, ip):
        if "/" in ip:
            ip = ip.split("/")[0]
        for idx, row in self.table.iterrows():
            if row["Destination"] == get_net_ip(ip, row["Mask"]):
                return row["NextHop"]
        return None

    def compress_net_group(x, y):
        if type(x) != list:
            x = [x]
        last = x[-1]
        if last["NextHop"] != y["NextHop"]:
            raise Exception("NextHop mismatch")
        if last["Interface"] != y["Interface"]:
            raise Exception("Interface mismatch")
        if last["Mask"] == y["Mask"]:
            if ip_to_int(
                get_broadcast(last["Destination"], last["Mask"])
            ) + 1 == ip_to_int(y["Destination"]):
                last["Mask"] -= 1
                last["MyCost"] = min(last["MyCost"], y["MyCost"])
                return reduce(RouteTable.compress_net_group, x)
            else:
                x.append(y)
                return x
        return x

    def merge_static_by_supernet(self):
        # filter out static routes
        static = self.table.query("Type == 'S'").copy(deep=True)
        # drop the static routes
        self.table = self.table.query("Type != 'S'")
        # group by next hop
        groups = static.groupby("NextHop")
        # iterate over groups
        for nexthop, group in groups:
            # get the destination ips
            dests = group["Destination"].values
            # compress the group to the minimum number of routes
            routes = reduce(
                RouteTable.compress_net_group, group.to_dict(orient="records")
            )
            # add the supernet to the table
            for route in routes:
                self.add_route(route)
    def generate_static_routing_commands(self, router=None):
        commands = []
        for idx, row in self.table.query("Type == 'S'").iterrows():
            command=f"ip route add {row['Destination']}/{row['Mask']} via {row['NextHop']} dev {row['Interface']}"
            if row["Configured"]:
                continue
            if router is None:
                commands.append(command)
            else:
                commands.append(f"lxc-attach -n {router} -- {command}")
        return commands
                    