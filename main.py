import numpy as np
from pprint import pprint
from net import Net
import pandas as pd
from mytty import get_tty_width
from colorama import Fore, Back, Style

BOLD = Style.BRIGHT


def main():
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.MAGENTA + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    routers = {
        "R01": {"eth0": ["br01"], "eth1": ["br02"], "eth2": ["br03"]},
        "R02": {"eth0": ["br03"], "eth1": ["br05"], "eth2": ["br04"]},
        "R03": {
            "eth0": ["br05"],
            "eth1": ["br08", "10.0.0.97/28"],
            "eth2": ["br06", "10.0.0.113/29"],
        },
        "R04": {
            "eth0": ["br08", "10.0.0.98/28"],
            "eth1": ["br09", "10.0.0.1/26"],
            "eth2": ["br07", "10.0.0.65/27"],
        },
        "R05": {
            "eth0": ["br0"],
            "eth1": ["br06", "10.0.0.114/29"],
            "eth2": ["br10", "10.0.0.121/29"],
        },
    }
    net = Net(routers)

    net.netdict["br01"]["devcount"] = 2 + 60
    net.netdict["br02"]["devcount"] = 2 + 20
    net.netdict["br03"]["devcount"] = 2 + 12
    net.netdict["br04"]["devcount"] = 2 + 6
    net.netdict["br05"]["devcount"] = 2 + 6
    net.assign_subnets("10.0.0.0/24")

    print(pd.DataFrame(net.netdict).T)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    _, commands = net.assign_ips(True)
    with open("commands.sh", "w") as f:
        f.write("\n".join(commands))
    print(pd.DataFrame(net.routers).T)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print("\n".join(commands))
    net.generate_routes()

    net.generate_non_direct_routes()
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    for router, routes in net.routes.items():
        print(router.center(get_tty_width()))
        print(routes.format_table())
        print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.BLUE + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    commands = net.generate_static_commands()
    print("\n".join(commands))
    print(Fore.GREEN + BOLD + "=" * get_tty_width() + Style.RESET_ALL)
    print(Fore.GREEN + BOLD + "=" * get_tty_width() + Style.RESET_ALL)


if __name__ == "__main__":
    main()
