#!/usr/bin/env bash

sudo vtysh -c "clear ip bgp $1 soft"
