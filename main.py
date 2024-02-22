# import numpy as np
import os

from colorama import Fore, Style
from rich.console import Console

# import pandas as pd

from mytty import get_tty_width
from net import Net

BOLD = Style.BRIGHT


def main():
    console = Console()
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    net = Net.read_scenario("P01-E02")

    # net.netdict["br01"]["devcount"] = 2 + 60
    # net.netdict["br02"]["devcount"] = 2 + 20
    # net.netdict["br03"]["devcount"] = 2 + 12
    # net.netdict["br04"]["devcount"] = 2 + 6
    # net.netdict["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/23")

    # print(pd.DataFrame(net.netdict).T)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    _, commands = net.assign_ips(True)
    for command in commands:
        # print(command)
        os.system(command)
    with open("commands.sh", "w", encoding="utf8") as f:
        f.write("\n".join(commands))
    # print(pd.DataFrame(net.routers).T)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print("\n".join(commands))
    net.generate_routes()

    net.generate_non_direct_routes()
    net.check_routes()
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    # for router, routes in net.routes.items():
    #     print(router.center(get_tty_width()))
    #     print(routes.format_table())
    #     print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    commands = net.generate_static_commands()
    print("\n".join(commands))
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    net.apply_configuration()
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    commands = [
        f"lxc-attach -n {router} -- vtysh -c 'show ip route'"
        for router in net.routers.keys()
    ]
    sorted_routes = sorted(net.routes.items(), key=lambda x: x[0])
    for router, routes in sorted_routes:
        console.print(router, justify="center", style="bold green")
        console.print(routes.format_table(), justify="center")
        os.system(f"lxc-attach -n {router} -- vtysh -c 'show ip route'")
        print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print("\n".join(commands))
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    working, total = net.check_all_connections(True)
    print(f"Working: {working} Total: {total} percentage: {working/total*100:.2f}%")
    print(Fore.GREEN + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.GREEN + BOLD + "=" * get_tty_width() + Style.RESET_ALL)


if __name__ == "__main__":
    main()
