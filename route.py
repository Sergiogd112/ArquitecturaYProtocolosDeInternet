from pprint import pprint
import pandas as pd
from colorama import Fore, Back, Style

BOLD = "\033[1m"


class RouteTable:
    def __init__(self):
        self.routes = pd.DataFrame(
            columns=[
                "Type",
                "Destination",
                "Cost",
                "NextHop",
                "Interface",
                "Mask",
                "Selected",
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
            }
        )

    def reset_routes(self):
        self.routes = pd.DataFrame(
            columns=[
                "Type",
                "Destination",
                "Cost",
                "NextHop",
                "Interface",
                "Mask",
                "Selected",
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
            }
        )
        return self.routes

    def add_route(self, route):
        pprint(route)
        self.routes = pd.concat([self.routes, pd.DataFrame([route])], ignore_index=True)
        self.routes = self.routes.drop_duplicates()
        self.routes = self.routes.sort_values(
            by=["Destination", "Mask"], ascending=[True, False]
        )
        self.routes = self.routes.reset_index(drop=True)
        return self.routes

    def split_rows(row):
        data = row.replace("  ", " ").replace("  ", " ").split(" ")
        Code = data[0].strip()
        network = data[1].strip()
        mask=None
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
            for col in zip(*[[len(str(c)) for c in row] for row in self.routes.values])
        ]
        headers = list(self.routes.columns)
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
        text=""
        text += separator + "\n"
        text += (headerstr) + "\n"
        for n, row in self.routes.iterrows():
            rowstr = "| " + RouteTable.format_code(row[0], lens[0]) + " "
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
                            if ">" in row[0]
                            else " " +str(c).center(l) + " "
                        )
                        for c, l in zip(row[1:], lens[1:])
                    ]
                )
                + "|"
            )
            if not ('"' in row[1]):
                text += separator + "\n"
            text += rowstr + "\n"
        text += separator + "\n"
        return text
