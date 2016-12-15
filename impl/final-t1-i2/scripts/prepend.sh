#!/usr/bin/env bash

sudo vtysh -c "conf term" -c "route-map rm permit $1" -c "set as-path prepend $2"
