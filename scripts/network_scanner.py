import ipaddress
import socket
from typing import Union

import ipcalc
import netifaces

try:
    addrs = netifaces.ifaddresses(netifaces.interfaces()[1])  # Choose the second interface since that's usually the main one.
    inet = addrs[netifaces.AF_INET][0]
    network = ipaddress.ip_network(str(ipcalc.IP(inet['addr'], mask=inet['netmask']).guess_network()))
    scanner_enabled = True
except:
    scanner_enabled = False


def scan_host(target_ip: str) -> Union[list, None]:
    if not scanner_enabled:
        return None
    open_ports = []
    ip = socket.gethostbyname(str(target_ip))
    for i in range(1, 65536):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        conn = s.connect_ex((ip, i))
        if conn == 0:
            open_ports.append(i)
            print('->', i)
        else:
            print(i)
        s.close()
    return open_ports


def scan_network() -> Union[dict, None]:
    if not scanner_enabled:
        return None
    hosts = {}
    for ip in network.hosts():
        print(ip)
        hosts[ip] = scan_host(str(ip))
    return hosts
