#!/bin/sh
# start.sh

BOT_PATH=home/pi/moby-bot

# reload environment
hash -r

sleep 5

cd /
cd $BOT_PATH

while [ true ]
    do
    python3 main.py
    sleep 5
done

cd /
