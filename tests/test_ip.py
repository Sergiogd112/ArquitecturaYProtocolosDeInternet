from ip import ip_to_int, int_to_ip, get_net_ip, get_broadcast

def test_ip_to_int():
    assert ip_to_int("10.0.0.0") == 167772160
def test_int_to_ip():
    assert int_to_ip(167772160) == "10.0.0.0"
def test_get_net_ip():
    assert get_net_ip("10.0.0.5", 24) == "10.0.0.0"
    assert get_net_ip("10.0.0.15", 29) == "10.0.0.8"
def test_get_broadcast():
    assert get_broadcast("10.0.0.5", 24) == "10.0.0.255"
    assert get_broadcast("10.0.0.15", 29) == "10.0.0.15"