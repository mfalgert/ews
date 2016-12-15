#!/usr/bin/env bash

vtysh -c "conf term" -c "router bgp $1" -c "neighbor $2 route-map rm out"
