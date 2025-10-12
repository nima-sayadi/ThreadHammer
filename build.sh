#!/bin/bash

source conf.cfg
root_path=$ROOT_PATH

buildLogfile="$root_path/logs/build.log"

isThreadHammerActive=false
while getopts ":t" opt; do
  case $opt in
    t)
      isThreadHammerActive=true
      ;;
    \?)
      echo "Usage: $0 [-t]" >&2
      exit 1
      ;;
  esac
done

if [ "$isThreadHammerActive" == false ];then
    echo -e "${BLACK_TXT}${BLUE_BG} Build ${COLOR_RESET} Building Blacksmith-Original ..."
    echo "Building Blacksmith-Original Started | $(date +%Y-%m-%d_%H-%M-%S)" >> "$buildLogfile"

    if [ -d "$root_path/Blacksmith-Original/build" ]; then
        echo -e "${BLACK_TXT}${BLUE_BG} Build ${COLOR_RESET} Removing Previous Blacksmith-Original Build..."
        rm -r "$root_path/Blacksmith-Original/build"
        echo -e "${BLACK_TXT}${BLUE_BG} Build ${COLOR_RESET} Previous Blacksmith-Original Build is Removed!"
    fi

    cd "$root_path/Blacksmith-Original/"
    mkdir build
    cd build
    cmake ../
    make -j$(nproc) >> "$buildLogfile" 2>&1

    echo -e "${BLACK_TXT}${BLUE_BG} Build ${COLOR_RESET} Building Blacksmith-Original done!"
    echo "Done building blacksmith-Original | $(date +%Y-%m-%d_%H-%M-%S)" >> "$buildLogfile"
else
    echo -e "${BLACK_TXT}${RED_BG} Build ${COLOR_RESET} Building ThreadHammer ..."
    echo "Building ThreadHammer Started | $(date +%Y-%m-%d_%H-%M-%S)" >> "$buildLogfile"

    if [ -d "$root_path/Blacksmith/build" ]; then
        echo -e "${BLACK_TXT}${RED_BG} Build ${COLOR_RESET} Removing Previous ThreadHammer Build..."
        rm "$root_path/logs/build.log"
        rm -r "$root_path/Blacksmith/build"
        echo -e "${BLACK_TXT}${RED_BG} Build ${COLOR_RESET} Previous ThreadHammer Build is Removed!"
    fi

    cd "$root_path/Blacksmith/"
    mkdir build
    cd build
    cmake ../
    make -j$(nproc) >> "$buildLogfile" 2>&1

    echo -e "${BLACK_TXT}${RED_BG} Build ${COLOR_RESET} Building ThreadHammer done!"
    echo "Done building ThreadHammer | $(date +%Y-%m-%d_%H-%M-%S)" >> "$buildLogfile"
fi
cd "$root_path"