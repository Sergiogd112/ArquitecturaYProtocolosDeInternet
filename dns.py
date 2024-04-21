from rich.prompt import Prompt, IntPrompt


class RR:
    def __init__(self, origin, TTL, dns_name, admin, inv_origin):
        self.origin = origin
        self.TTL = TTL
        self.dns_name = dns_name
        self.admin = admin
        self.inv_origin = inv_origin
        self.NS = []
        self.inv_NS = []
        self.MX = []
        self.inv_MX = []


def generate_zone(origin, ip, mask, file, invfile, dns_ip=None, slave_ip=None):

    invorigin = ".".join(ip.split(".")[: mask // 8][::-1]) + ".in-addr.arpa"
    # TTL=IntPrompt.ask("TTL:" default=64000)
    name_conf_loca_master = (
        f'zone "{origin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{file}";\n'
        + (
            ("    allow-transfer { " + f"{slave_ip};" + " };\n")
            if slave_ip != "" and slave_ip is not None
            else ""
        )
        + "};\n\n"
        + f'zone "{invorigin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{invfile}";\n'
        + (
            ("    allow-transfer { " + f"{slave_ip};" + " };\n")
            if slave_ip != "" and slave_ip is not None
            else ""
        )
        + "};\n"
    )
    if slave_ip == None:
        return name_conf_loca_master
    name_conf_loca_slave = (
        f'zone "{origin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{file}";\n'
        + "    masters { "
        + f"{dns_ip};"
        + " };\n"
        + "    masterfile-format text;\n"
        + "};\n\n"
        + f'zone "{invorigin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{invfile}";\n'
        + "    masters { "
        + f"{dns_ip};"
        + " };\n"
        + "    masterfile-format text;\n"
        + "};\n"
    )

    return name_conf_loca_master, name_conf_loca_slave


def run():
    origin = Prompt.ask("Enter the origin:")
    sides = Prompt.ask("Enter net ip (IP/MASK): ").split("/")
    ip = sides[0]
    if len(sides) == 1:
        mask = IntPrompt.ask("Enter the net mask", choices=[0, 8, 16, 24])
    else:
        mask = int(sides[1])
    dns_ip = Prompt.ask("enter the master dns ip:")
    dns_name = Prompt.ask("enter the master dns name:")
    slave_ip = Prompt.ask("enter the slave dns ip:")
    if slave_ip == "":
        slave_name = Prompt.ask("Enter the name of the slave:")
    dbfile = Prompt.ask("File for the direct RR:", default=origin.slit(".")[0] + ".db")
    invdbfile = Prompt.ask(
        "File for the inverse RR:", default=origin.slit(".")[0] + "_inv.db"
    )

    if not (origin.endswith(".")):
        origin = origin + "."
