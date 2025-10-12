#!/bin/bash

source conf.cfg
root_path=$ROOT_PATH
log_file="$root_path/logs/compress.log"

echo -e "${BLUE_BG} Compressor ${COLOR_RESET} Compressing Results..."

fileName="logs_$(date +%Y-%m-%d__%H-%M).zip"

find "$root_path" -maxdepth 1 -type f -name '*.json' -exec mv -- {} "$root_path/logs/" \;
zip -r "$fileName" "$root_path/logs" > "$log_file" 2>&1
mv "$root_path/$fileName" "$root_path/results/$fileName"

echo -e "${BLUE_BG} Compressor ${COLOR_RESET} All Results are zipped & stored in /results path!"
