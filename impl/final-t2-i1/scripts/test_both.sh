#!/usr/bin/env bash

sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/filter_out.sh 500 $1"
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/clear_out.sh $1"
sleep 50
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/no_filter_out.sh 500 $1"
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/clear_out.sh $1"
sleep 50
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/filter_out.sh 500 $1"
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/clear_out.sh $1"
sleep 50
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/no_filter_out.sh 500 $1"
sudo sh scripts/mx.sh "500_r1" "sudo sh /home/marcus/ews/impl/final-t2-i1/scripts/clear_out.sh $1"
