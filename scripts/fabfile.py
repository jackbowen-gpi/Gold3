"""
Fabric deployment file.

To update all server nodes, type:

  fab update

You must have fabric installed. See http://www.nongnu.org/fab/ for more details.
"""

import getpass

# from fabric.api import *
from fabric2 import Connection, task


def update_apache(user, password):
    """Run svn update and restart apache so the changes take effect."""
    conn = Connection(
        host="apache1.na.graphicpkg.pri",
        user="gchub",
        connect_kwargs={"password": "1987tigersdontsurf"},
    )
    conn.run("svn update --password %s --username %s /home/gchub/gchub_db" % (password, user))
    conn.run("touch /home/gchub/gchub_db/gchub_db/apache/wsgi_conf.py")


def update_db(user, password):
    """Run svn update and restart apache so the changes take effect."""
    conn = Connection(
        host="db2017.na.graphicpkg.pri",
        user="gchub",
        connect_kwargs={"password": "1987tigersdontsurf"},
    )
    conn.run("svn update --password %s --username %s /home/gchub/gchub_db" % (password, user))
    conn.run("touch /home/gchub/gchub_db/gchub_db/apache/wsgi_conf.py")


def update_fedex(user, password):
    """Run svn update and restart apache so the changes take effect."""
    conn = Connection(
        host="fedex.na.graphicpkg.pri",
        user="admin",
        connect_kwargs={"password": "1987tigersdontsurf"},
    )
    conn.run("svn update --password %s --username %s /home/admin/gchub_db" % (password, user))
    conn.run("touch /home/admin/gchub_db/gchub_db/apache/wsgi_conf.py")


@task
def update(ctx):
    """Update GOLD and restart apache on the following sets of servers."""
    user = input("Enter SVN Username: ")
    password = getpass.getpass("Enter SVN Password: ")

    update_apache(user, password)
    update_db(user, password)
    update_fedex(user, password)
