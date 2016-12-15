#!/usr/bin/env bash

vtysh -c "conf term" -c "router bgp $1" -c "no neighbor $2 route-map rm out"
