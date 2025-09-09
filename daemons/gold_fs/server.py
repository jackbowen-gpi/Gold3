#!/usr/bin/env python
"""This is a simple UDP server that listens for filesystem UDP datagrams; commands are routed to the command handler (handler.py) via getattr()."""

import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

from . import handlers


class EchoUDP(DatagramProtocol):
    """UDP server protocol that routes filesystem commands to handlers.

    Each datagram is split into a command and args; handlers are looked up on
    the `handlers` module using a `cmd_<name>` naming convention.
    """

    def __init__(self, reactor):
        self.reactor = reactor

    def datagramReceived(self, datagram, address):
        """Parse the datagram and pass it to the correct command handler in handlers.py."""
        cmd_split = datagram.split()
        # print "SPLIT", cmd_split

        cmd_name = cmd_split[0]
        cmd_args = cmd_split[1:]
        cmd_function_str = "cmd_%s" % cmd_name
        try:
            cmd_func = getattr(handlers, cmd_function_str)
        except AttributeError:
            print("! Invalid command: %s" % cmd_name)
            return

        cmd_func(cmd_args, self)


def main():
    """Start the GOLD FS UDP server and begin the reactor loop.

    This function is intentionally small so it can be run as a script to
    start the daemon from the command line.
    """
    reactor.listenUDP(8000, EchoUDP(reactor))
    print("* GOLD FS server started.")
    reactor.run()


if __name__ == "__main__":
    main()
