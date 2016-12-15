#!/bin/bash

# perform test
echo "removing old procsses..."
sudo pkill -f -9 send_from_peers.py
sudo pkill -f -9 test_both.sh
sudo pkill -f -9 test_clear_out.sh
sudo pkill -f -9 test_prepend.sh
sudo pkill -f -9 test_wd.sh
sudo pkill -f -9 test_an.sh
echo "test.sh now running..."

sudo python scripts/send_from_peers.py &
sleep="$(shuf -i 33-63 -n 1)"
sleep $sleep

while true; do
	sudo sh scripts/test_wd.sh "20.0.7.1"
	sleep="$(shuf -i 101-111 -n 1)"
	sleep $sleep

	sudo sh scripts/test_an.sh "20.0.7.1"
	sleep="$(shuf -i 101-111 -n 1)"
	sleep $sleep
done
