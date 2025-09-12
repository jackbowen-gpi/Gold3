"""
Small helper to send a UDP shutdown datagram to the Gold FS server.

Run this module as a script to exercise sending a shutdown packet to the
file-server; importing the module does not perform network operations.
"""

from socket import AF_INET, SOCK_DGRAM, socket


# Don't perform network operations at import-time. Run this module as a
# script to exercise sending a shutdown datagram.
def send_shutdown(host="172.23.8.49", port=8000):
    """
    Send a shutdown UDP datagram to the given host:port.

    This is intended for manual test runs only.
    """
    addr = (host, port)
    s = socket(AF_INET, SOCK_DGRAM)
    data = b"shutdown"
    num_sent = 0
    while num_sent < len(data):
        num_sent += s.sendto(data[num_sent:], addr)
    s.close()


if __name__ == "__main__":
    send_shutdown()
