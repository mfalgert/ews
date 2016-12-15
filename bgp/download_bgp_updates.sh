#!/bin/bash

# Syntax: sh download_bgp_updates.sh rrc month day
# This will download all BGP updates collected by a specific rcc at a specific month and day
# RCCs, months, and days must be numbers of length 2 (january = 01 etc)

# RRCs and their locations (only RRCs which still collect data as of 2016 are included):
# 00 - Amsterdam
# 01 - London
# 04 - Geneva
# 05 - Vienna
# 06 - Otemachi
# 07 - Stockholm
# 10 - Milan
# 11 - New York
# 12 - Frankfurt
# 13 - Moscow
# 14 - Palo Alto
# 15 - Sao Paulo
# 16 - Miami

DOWNLOAD_DIR=/home/marcus/ews/bgp/dumps/rrc$1/2016.$2.$3/

mkdir $DOWNLOAD_DIR
wget -P $DOWNLOAD_DIR -r -np -nd --reject "index.html*" -e robots=off --accept='updates.2016'"$2$3"'*.gz' http://data.ris.ripe.net/rrc$1/2016.$2/

