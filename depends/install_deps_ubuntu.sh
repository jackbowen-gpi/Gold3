#!/bin/bash
# Automagically installs GOLD dependencies on Ubuntu.
# You'll have to hit "yes" or "y" a few times so pay attention.

sudo apt-get update

sudo apt-get upgrade python3-setuptools
sudo apt-get upgrade python3-pip
sudo apt-get upgrade inkscape

# Django
sudo pip3 install django-formtools==2.2
sudo pip3 install django-extensions==2.2.3
sudo pip3 install django-localflavor==1.4.1
# wiki client editor
sudo pip3 install mwclient==0.8.2
# These next two are prereqs for psycopg2
sudo apt-get upgrade libpq-dev
sudo apt-get upgrade python3-dev
# Linux ODBC reqs
sudo apt-get upgrade tdsodbc
sudo pip3 install psycopg2==2.7.5
sudo pip3 install xlrd==1.0
sudo pip3 install reportlab==3.3
# Prereq for Fabric
sudo pip3 install pycrypto==2.6.1
sudo pip3 install fabric==2.5.0
sudo pip3 install docutils==0.13.1
#Pre-Req for Twisted
sudo pip3 install incremental==17.5.0
sudo pip3 install twisted==16.6
#Pre-Req for suds
sudo pip3 install client==0.0.1
sudo pip3 install suds==0.4
sudo pip3 install beautifulsoup4
# Numpy takes while to install and might appear to be stuck. Just give it 5 minutes.
sudo pip3 install numpy==1.12
sudo pip3 install networkx==1.11
sudo pip3 install openpyxl==2.6.1
# Prereq for unixodbc
sudo pip3 install pytest-runner
# Prereq for pyodbc
sudo apt-get upgrade unixodbc unixodbc-dev
sudo pip3 install pyodbc==4.0.1
sudo pip3 install svglib==0.8.1
sudo pip3 install fedex==2.4
sudo pip3 install colormath==3
sudo pip3 install wget==3.2
sudo easy_install scons==2.5.1
sudo pip3 install gntp==1.0.3
#PreReq for pysftp
apt-get install build-essential libssl-dev libffi-dev python-dev
sudo pip3 install cryptography==2.8
sudo pip3 install pysftp==0.2.9
#PreReq for secrets
sudo pip3 install pyopenssl==19.1.0
sudo apt-get install python-dev libldap2-dev libsasl2-dev libssl-dev
#sudo pip3 install python3-ldap==0.9.8.4
sudo pip3 install secrets==1.0.2
sudo pip3 install exifread==2.1.2

#Doing this at the end to ensure that django 2.2 is installed. Other packages install later versions of django.
sudo pip3 install django==2.2


echo "-- Installation Complete --"
