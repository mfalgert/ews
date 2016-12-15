#!/usr/bin/env bash

for file in *
do
	sudo dos2unix "$file"
done
