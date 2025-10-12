#!/bin/bash

originalBlacksmith=false
while getopts ":o" opt; do
  case $opt in
    o)
      originalBlacksmith=true
      ;;
    \?)
      echo "Usage: $0 [-o]" >&2
      exit 1
      ;;
  esac
done

if [ "$originalBlacksmith" == false ];then
    scp -r Blacksmith/src/ root@10.42.42.11:/root/ThreadHammer/Blacksmith
    scp -r Blacksmith/include/ root@10.42.42.11:/root/ThreadHammer/Blacksmith
else
    scp -r Blacksmith-Original/src/ root@10.42.42.11:/root/ThreadHammer/Blacksmith
    scp -r Blacksmith-Original/include/ root@10.42.42.11:/root/ThreadHammer/Blacksmith
fi
