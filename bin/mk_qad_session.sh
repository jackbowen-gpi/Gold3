#!/bin/bash
# This creates a direct SQL session to the remote etools database.
iodbctest "DSN=datawarehouse;UID=fsbuser;PWD=fsbIT2008"
