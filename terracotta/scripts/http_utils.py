"""scripts/http_utils.py

Various utilities to work with HTTP connections
"""

from typing import Optional, Sequence


def check_socket(host: str, port: int) -> bool:
    """Check if given port can be listened to"""
    import socket
    from contextlib import closing

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(2)
        try:
            sock.bind((host, port))
            sock.listen(1)
            return True
        except socket.error:
            return False


def find_open_port(port_range: Sequence[int]) -> Optional[int]:
    """Return first open port in port_range, or None if no open port is found"""
    for port_candidate in port_range:
        if check_socket('localhost', port_candidate):
            return port_candidate

    return None
