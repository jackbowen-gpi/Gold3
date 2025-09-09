"""Send a UDP datagram to shutdown and restart the FS daemon running on master."""

import bin_functions

bin_functions.setup_paths()
from gchub_db.includes import fs_api

fs_api.restart_fs_server()
