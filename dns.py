from typing import List
import tomllib
import os

# from rich.prompt import Prompt, IntPrompt,
from rich.prompt import Confirm
from rich.console import Console


class RRTable:
    def __init__(self, origin, ttl, dns_name, admin, inv_origin, ip, serial=2018111201):
        self.origin = origin
        self.ttl = ttl
        self.dns_name = dns_name
        self.admin = admin
        self.inv_origin = inv_origin
        self.octets = 7 - len(inv_origin.split("."))
        self.ip = ip
        self.serial = serial
        self.inv_name = (
            self.dns_name
            if self.dns_name.endswith(".")
            else self.dns_name + "." + self.origin
        )
        self.inv_admin = (
            self.admin if self.admin.endswith(".") else self.admin + "." + self.origin
        )
        self.ns = []

        self.inv_ns = []
        self.mx = []
        self.a = []
        self.ptr = []
        self.cname = []
        self.inv_cname = []
        self.add_ns(self.dns_name, self.ip)

    def add_ns(self, name, ip):

        if ["", name] not in self.ns:
            self.ns.append(["", name])
            self.inv_ns.append(
                ["", name if name.endswith(".") else name + "." + self.origin]
            )

        self.add_a(name, ip)

    def add_mx(self, name, ip, priority):
        for mx in self.mx:
            if mx[1] == name:
                mx[0] = priority
                return
        self.mx.append([priority, name])
        self.add_a(name, ip)

    def add_a(self, name, ip):
        for i, a in enumerate(self.a):
            if a[0] == name:
                self.a[i][1] = ip

                self.ptr[i][0] = ".".join(ip.split(".")[-self.octets :][::-1])
                return
            elif a[1] == ip:
                self.a[i][0] = name
                self.ptr[i][1] = (
                    name if name.endswith(".") else name + "." + self.origin
                )
                return

        self.a.append([name, ip])
        self.ptr.append(
            [
                ".".join(ip.split(".")[-self.octets :][::-1]),
                name if name.endswith(".") else name + "." + self.origin,
            ]
        )

    def add_cname_inv(self, alias, name):
        self.inv_cname.append([alias, name])

    def add_sub(self, dns_name, domain, dns_ip, iprange, mask, ips):
        self.ns.append([domain, dns_name + "." + domain])
        segm = iprange.split(".")[-self.octets :]
        segm[-1] += "/" + str(mask)
        self.inv_ns.append(
            [
                ".".join(segm[::-1]),
                (
                    dns_name + "." + domain
                    if domain.endswith(".")
                    else dns_name + "." + domain + "." + self.origin
                ),
            ]
        )

        for ip in ips:

            self.add_cname_inv(
                ".".join(ip.split(".")[-self.octets :][::-1]),
                ".".join(ip.split(".")[-self.octets :][::-1])
                + "."
                + ".".join(segm[::-1]),
            )

    def generate_db_file(self):
        dir_content = f"$ORIGIN {self.origin}\n"
        dir_content += f"$TTL {self.ttl}\n"
        dir_content += "\n"
        dir_content += f"@\tIN\tSOA\t{self.dns_name} {self.admin} (\n"
        dir_content += "\t\t\t2018111201\n"  # serial
        dir_content += "\t\t\t86400\n"  # refresh
        dir_content += "\t\t\t7200\n"  # retry
        dir_content += "\t\t\t2419200\n"  # expire
        dir_content += "\t\t\t3600)\n"  # neg. TTL
        for row in self.ns:
            dir_content += f"{row[0]}\t\tNS\t{row[1]}\n"
        for row in self.mx:
            dir_content += f"\t\tMX\t{row[0]} {row[1]}\n"
        for row in self.a:
            cell0 = row[0] if row[0] != "" else "\t"
            dir_content += f"{cell0}\t\tA\t{row[1]}\n"
        inv_content = f"$ORIGIN {self.inv_origin}\n"
        inv_content += f"$TTL {self.ttl}\n"
        inv_content += "\n"
        inv_content += f"@\tIN\tSOA\t{self.inv_name} {self.inv_admin} (\n"
        inv_content += f"\t\t\t{self.serial}\n"  # serial
        inv_content += "\t\t\t86400\n"  # refresh
        inv_content += "\t\t\t7200\n"  # retry
        inv_content += "\t\t\t2419200\n"  # expire
        inv_content += "\t\t\t3600)\n"  # neg. TTL
        for row in self.inv_ns:
            inv_content += f"{row[0]}\t\tNS\t{row[1]}\n"
        for row in self.ptr:
            inv_content += f"{row[0]}\t\tPTR\t{row[1]}\n"
        for row in self.inv_cname:
            inv_content += f"{row[0]}\t\tCNAME\t{row[1]}\n"
        return dir_content, inv_content

    def print(self):
        dir_content, inv_content = self.generate_db_file()
        Console().print("Direct", style="bold cyan")
        Console().print(dir_content)
        Console().print("Inverse", style="bold magenta")
        Console().print(inv_content)


def generate_zone(
    origin: str,
    ip: str,
    mask: int,
    file: str,
    invfile: str,
    dns_ip: str = None,
    slave_ips: List[str] = None,
) -> tuple[str, None] | tuple[str, List[str]]:

    invorigin = ".".join(ip.split(".")[: mask // 8][::-1]) + ".in-addr.arpa"
    # TTL=IntPrompt.ask("TTL:" default=64000)
    name_conf_loca_master = (
        f'zone "{origin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{file}";\n'
        + (
            ("    allow-transfer { " + ";".join(slave_ips) + ";" + " };\n")
            if slave_ips is not None and slave_ips != ""
            else ""
        )
        + "};\n\n"
        + f'zone "{invorigin}"'
        + " {\n"
        + "    type master;\n"
        + f'    file "{invfile}";\n'
        + (
            ("    allow-transfer { " + ";".join(slave_ips) + ";" + " };\n")
            if slave_ips is not None and slave_ips != ""
            else ""
        )
        + "};\n"
    )
    if slave_ips is None or len(slave_ips) == 0:
        return name_conf_loca_master, None

    name_conf_loca_slaves = [
        (
            f'zone "{origin}"'
            + " {\n"
            + "    type slave;\n"
            + f'    file "{file}";\n'
            + "    masters { "
            + f"{dns_ip};"
            + " };\n"
            + "    masterfile-format text;\n"
            + "};\n\n"
            + f'zone "{invorigin}"'
            + " {\n"
            + "    type slave;\n"
            + f'    file "{invfile}";\n'
            + "    masters { "
            + f"{dns_ip};"
            + " };\n"
            + "    masterfile-format text;\n"
            + "};\n"
        )
        for ip in slave_ips
    ]

    return name_conf_loca_master, name_conf_loca_slaves


# def run():
#     origin = Prompt.ask("Enter the origin:")
#     sides = Prompt.ask("Enter net ip (IP/MASK): ").split("/")
#     ip = sides[0]
#     if len(sides) == 1:
#         mask = IntPrompt.ask("Enter the net mask", choices=[0, 8, 16, 24])
#     else:
#         mask = int(sides[1])
#     dns_ip = Prompt.ask("enter the master dns ip:")
#     dns_name = Prompt.ask("enter the master dns name:")
#     slave_ip = Prompt.ask("enter the slave dns ip:")
#     slave_name = ""
#     if slave_ip != "":
#         slave_name = Prompt.ask("Enter the name of the slave:")
#     dbfile = Prompt.ask("File for the direct RR:", default=origin.slit(".")[0] + ".db")
#     invdbfile = Prompt.ask(
#         "File for the inverse RR:", default=origin.slit(".")[0] + "_inv.db"
#     )
#     masterconf, slaveconf = generate_zone(
#         origin, ip, mask, dbfile, invdbfile, dns_ip, slave_ip
#     )
#     console = Console()
#     console.print(masterconf)
#     console.print(slaveconf)

#     if not (origin.endswith(".")):
#         origin = origin + "."


def parse_toml(file: str, apply=False):
    console = Console()
    with open(file, "rb") as f:
        data = tomllib.load(f)
    console.print(data)
    origin = [key for key in data.keys() if "RR" != key][0]
    conf = data[origin]
    rr_data = data[origin]["RR"]

    master_conf, slave_confs = generate_zone(
        origin,
        conf["iprange"],
        conf["mask"],
        conf["dirfile"],
        conf["invfile"],
        conf["ip_master"],
        conf["ip_slaves"],
    )
    console.print(conf["master"], style="bold cyan")
    console.print(master_conf)
    for slave, slave_conf in zip(conf["slaves"], slave_confs):
        console.print(slave, style="bold magenta")
        console.print(slave_conf)
    if not (origin.endswith(".")):
        origin = origin + "."
    invorigin = (
        ".".join(conf["iprange"].split(".")[: conf["mask"] // 8][::-1])
        + ".in-addr.arpa."
    )

    rrtable = RRTable(
        origin,
        conf["ttl"],
        conf["master_hostname"],
        conf["admin"],
        invorigin,
        conf["ip_master"],
        conf["serial"],
    )
    # rrtable.print()
    # console.print(rr_data)
    for rr in rr_data:
        # console.print(rr)
        match rr["type"]:
            case "NS":
                rrtable.add_ns(rr["name"], rr["ip"])
                continue
            case "MX":
                rrtable.add_mx(rr["name"], rr["ip"], rr["priority"])
                continue
            case "A":
                rrtable.add_a(rr["name"], rr["ip"])
                continue
    rrtable.print()
    if "subdomain" in conf:
        for subdomain in conf["subdomain"]:
            rrtable.add_sub(
                subdomain["dns_name"],
                subdomain["subdomain"],
                subdomain["dns_ip"],
                subdomain["iprange"],
                subdomain["mask"],
                subdomain["ips"],
            )
        rrtable.print()
    lxc_path = "/var/lib/lxc/"
    if not apply:
        return master_conf, slave_confs, rrtable

    if not os.path.exists(lxc_path):
        return master_conf, slave_confs, rrtable
    for name, conf_cont in zip(
        [conf["master"]] + conf["slaves"], [master_conf] + slave_confs
    ):
        with open(
            os.path.join(lxc_path, name, "rootfs", "etc", "bind", "named.conf.local"),
            "w",
        ) as f:
            f.write(conf_cont)
        os.system(f"lxc-attach -n {name} -- named-checkconf")
    dircon, invcon = rrtable.generate_db_file()
    with open(
        os.path.join(
            lxc_path, conf["master"], "rootfs", "var", "cache", "bind", conf["dirfile"]
        ),
        "w",
    ) as f:
        f.write(dircon)
    os.system(
        f"lxc-attach -n {conf['master']} -- named-checkzone {origin} "
        + f"/var/cache/bind/{conf['dirfile']}"
    )

    with open(
        os.path.join(
            lxc_path, conf["master"], "rootfs", "var", "cache", "bind", conf["invfile"]
        ),
        "w",
    ) as f:
        f.write(invcon)
    os.system(
        f"lxc-attach -n {conf['master']} -- named-checkzone {invorigin} "
        + f"/var/cache/bind/{conf['invfile']}"
    )
    if Confirm.ask("Restart bind"):
        for name in [conf["master"]] + conf["slaves"]:
            os.system(f"lxc-attach -n {name} -- systemctl restart bind9")

    return master_conf, slave_confs, rrtable


if __name__ == "__main__":
    parse_toml("dns.toml")
