#!/bin/sh
# start.sh

BOT_PATH=home/pi/moby-bot

cd /
cd $BOT_PATH

while [ true ]
do
    python3 main.py
    sleep 5
done

cd /
