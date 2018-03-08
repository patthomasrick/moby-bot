#!/bin/sh
# start.sh

clear
echo "----STARTING MOBY----\n"

while [ true ]
    do
    python3 main.py
    echo "\n\n----RESTARTING MOBY----\n"
    sleep 5
done

cd /
