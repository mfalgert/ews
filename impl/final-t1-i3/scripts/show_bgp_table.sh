#!/usr/bin/env bash

arg=${1-}  

vtysh -c "show ip bgp $arg"
