from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from dns import *


def test_genrate_zone_master():
    console = Console()
    expected = """zone "lab.api" {
    type master;
    file "lab.db";
};

zone "1.0.10.in-addr.arpa" {
    type master;
    file "lab_inv.db";
};
"""
    result = generate_zone("lab.api", "10.0.1.0", 24, "lab.db", "lab_inv.db")
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
    expected_slave = """zone "lab.api" {
    type master;
    file "lab.db";
    masters { 10.0.1.2; };
    masterfile-format text;
};

zone "1.0.10.in-addr.arpa" {
    type master;
    file "lab_inv.db";
    masters { 10.0.1.2; };
    masterfile-format text;
};
"""
    result_master, result_slave = generate_zone(
        "lab.api", "10.0.1.0", 24, "lab.db", "lab_inv.db", "10.0.1.2", "10.0.1.3"
    )
    columns = Columns()
    subcolumns_master = Columns()
    subcolumns_master.add_renderable(Panel(expected_master, title="Expected"))
    subcolumns_master.add_renderable(Panel(result_master, title="Result"))
    columns.add_renderable(Panel(subcolumns_master, title="Master"))
    subcolumns_slave = Columns()
    subcolumns_slave.add_renderable(Panel(expected_slave, title="Expected"))
    subcolumns_slave.add_renderable(Panel(result_slave, title="Result"))
    columns.add_renderable(Panel(subcolumns_slave, title="Slave"))
    console.print(columns)
    assert result_master == expected_master
    assert result_slave == expected_slave
