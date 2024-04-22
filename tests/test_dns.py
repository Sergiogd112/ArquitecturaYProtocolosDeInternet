from pytest import fixture
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from dns import RRTable, generate_zone, parse_toml


@fixture
def rr():
    return RRTable("lab.api.", 64000, "ns", "admin", "1.0.10.in-addr.arpa.", "10.0.1.2")


@fixture
def console():
    return Console(width=160)


def test_genrate_zone_master(console):
    expected = """zone "lab.api" {
    type master;
    file "lab.db";
};

zone "1.0.10.in-addr.arpa" {
    type master;
    file "lab_inv.db";
};
"""
    result, _ = generate_zone("lab.api", "10.0.1.0", 24, "lab.db", "lab_inv.db")
    columns = Columns()
    columns.add_renderable(Panel(expected))
    columns.add_renderable(Panel(result))
    console.print(columns)
    assert result == expected


def test_genrate_zone_master_slave():
    console = Console()
    expected_master = """zone "lab.api" {
    type master;
    file "lab.db";
    allow-transfer { 10.0.1.3; };
};

zone "1.0.10.in-addr.arpa" {
    type master;
    file "lab_inv.db";
    allow-transfer { 10.0.1.3; };
};
"""
    expected_slaves = [
        """zone "lab.api" {
    type slave;
    file "lab.db";
    masters { 10.0.1.2; };
    masterfile-format text;
};

zone "1.0.10.in-addr.arpa" {
    type slave;
    file "lab_inv.db";
    masters { 10.0.1.2; };
    masterfile-format text;
};
"""
    ]
    result_master, result_slaves = generate_zone(
        "lab.api", "10.0.1.0", 24, "lab.db", "lab_inv.db", "10.0.1.2", ["10.0.1.3"]
    )

    columns = Columns()
    subcolumns_master = Columns()
    subcolumns_master.add_renderable(Panel(expected_master, title="Expected"))
    subcolumns_master.add_renderable(Panel(result_master, title="Result"))
    columns.add_renderable(Panel(subcolumns_master, title="Master"))
    subcolumns_slave = Columns()
    subcolumns_slave.add_renderable(Panel(expected_slaves[0], title="Expected"))
    subcolumns_slave.add_renderable(Panel(result_slaves[0], title="Result"))
    columns.add_renderable(Panel(subcolumns_slave, title="Slave"))
    console.print(columns)
    assert result_master == expected_master
    assert result_slaves[0] == expected_slaves[0]


def test_rr_simple_dir(rr, console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA\tns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
ns		A	10.0.1.2
"""
    result, _ = rr.generate_db_file()

    columns = Columns(width=80)
    columns.add_renderable(Panel(str(expected)))
    columns.add_renderable(Panel(str(result)))
    console.print(columns)
    assert result == expected


def test_rr_simple_invr(rr, console):
    expected = """$ORIGIN 1.0.10.in-addr.arpa.
$TTL 64000

@	IN	SOA\tns.lab.api. admin.lab.api. (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns.lab.api.
2		PTR	ns.lab.api.
"""
    _, result = rr.generate_db_file()

    columns = Columns(width=40)
    columns.add_renderable(Panel(str(expected)))
    columns.add_renderable(Panel(str(result)))
    console.print(columns)
    assert result == expected


def test_rr_mx_dir(rr, console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA\tns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
		MX	10 mail
ns		A	10.0.1.2
mail		A	10.0.1.4
"""
    rr.add_mx("mail", "10.0.1.4", 10)
    result, _ = rr.generate_db_file()

    columns = Columns()
    columns.add_renderable(Panel(str(expected), width=70))
    columns.add_renderable(Panel(str(result), width=70))
    console.print(columns)
    assert result == expected


def test_rr_mx_invr(rr, console):
    expected = """$ORIGIN 1.0.10.in-addr.arpa.
$TTL 64000

@	IN	SOA\tns.lab.api. admin.lab.api. (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns.lab.api.
2		PTR	ns.lab.api.
4		PTR	mail.lab.api.
"""
    rr.add_mx("mail", "10.0.1.4", 10)
    _, result = rr.generate_db_file()

    columns = Columns(width=40)
    columns.add_renderable(Panel(str(expected)))
    columns.add_renderable(Panel(str(result)))
    console.print(columns)
    assert result == expected


def test_rr_ns_dir(rr, console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA\tns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
		NS	ns2
ns		A	10.0.1.2
ns2		A	10.0.1.3
"""
    rr.add_ns("ns2", "10.0.1.3")
    result, _ = rr.generate_db_file()

    columns = Columns()
    columns.add_renderable(Panel(str(expected), width=70))
    columns.add_renderable(Panel(str(result), width=70))
    console.print(columns)
    assert result == expected


def test_rr_ns_invr(rr, console):
    expected = """$ORIGIN 1.0.10.in-addr.arpa.
$TTL 64000

@	IN	SOA\tns.lab.api. admin.lab.api. (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns.lab.api.
		NS	ns2.lab.api.
2		PTR	ns.lab.api.
3		PTR	ns2.lab.api.
"""
    rr.add_ns("ns2", "10.0.1.3")
    _, result = rr.generate_db_file()

    columns = Columns(width=40)
    columns.add_renderable(Panel(str(expected)))
    columns.add_renderable(Panel(str(result)))
    console.print(columns)
    assert result == expected


def test_rr_a_dir(rr, console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA\tns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
ns		A	10.0.1.2
www		A	10.0.1.5
"""
    rr.add_a("www", "10.0.1.5")
    result, _ = rr.generate_db_file()

    columns = Columns()
    columns.add_renderable(Panel(str(expected), width=70))
    columns.add_renderable(Panel(str(result), width=70))
    console.print(columns)
    assert result == expected


def test_rr_a_invr(rr, console):
    expected = """$ORIGIN 1.0.10.in-addr.arpa.
$TTL 64000

@	IN	SOA\tns.lab.api. admin.lab.api. (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns.lab.api.
2		PTR	ns.lab.api.
5		PTR	www.lab.api.
"""
    rr.add_a("www", "10.0.1.5")
    _, result = rr.generate_db_file()

    columns = Columns(width=40)
    columns.add_renderable(Panel(str(expected)))
    columns.add_renderable(Panel(str(result)))
    console.print(columns)
    assert result == expected


def test_read_toml_dir(console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA	ns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
		NS	ns2
		MX	10 mail
ns		A	10.0.1.2
ns2		A	10.0.1.3
mail		A	10.0.1.4
www		A	10.0.1.5
usr1		A	10.0.1.66
usr2		A	10.0.1.98
"""
    _, _, rrtable = parse_toml("tests/dns.toml")
    result, _ = rrtable.generate_db_file()
    columns = Columns()
    columns.add_renderable(Panel(str(expected), width=70))
    columns.add_renderable(Panel(str(result), width=70))
    console.print(columns)
    assert result == expected


def test_read_toml_sub_dir(console):
    expected = """$ORIGIN lab.api.
$TTL 64000

@	IN	SOA	ns admin (
			2018111201
			86400
			7200
			2419200
			3600)
		NS	ns
		NS	ns2
subgrup		NS	ns.subgrup
		MX	10 mail
ns		A	10.0.1.2
ns2		A	10.0.1.3
mail		A	10.0.1.4
www		A	10.0.1.5
usr1		A	10.0.1.66
usr2		A	10.0.1.98
"""
    _, _, rrtable = parse_toml("tests/dns_sub.toml")
    result, _ = rrtable.generate_db_file()
    columns = Columns()
    columns.add_renderable(Panel(str(expected), width=70))
    columns.add_renderable(Panel(str(result), width=70))
    console.print(columns)
    assert result == expected
