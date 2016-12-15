#!/usr/bin/python

# clear log files
echo "*** Clearing log files"
sudo rm -r /var/log/mininext/*
sudo rm logg.log

# mininet cleanup and startup
echo "*** Killing old mininet processes"
sudo pkill -f -9 mininet
sudo pkill -f -9 trigger_timers
sudo pkill -f -9 test.sh
sudo pkill -f -9 trigger_router
sudo pkill -f -9 send_from_peers

echo "*** Cleaning up mininet"
sudo mn -c

echo "*** Starting mininet"
sudo python start.py
