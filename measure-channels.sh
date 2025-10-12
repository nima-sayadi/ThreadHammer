#!/bin/bash

source conf.cfg
root_path=$ROOT_PATH

mkdir -p "$root_path/results"
mkdir -p "$root_path/logs"

output_name=""
repetition=1

# Parse flags
while getopts "o:r:" opt; do
  case $opt in
    o)
      output_name="$OPTARG"
      ;;
    r)
      repetition="$OPTARG"
      ;;
    \?)
      echo "Usage: $0 -o output_name [-r repetition]"
      exit 1
      ;;
  esac
done

if [ -z "$output_name" ]; then
  echo "Error: -o (output name) is required"
  echo "Usage: $0 -o output_name"
  exit 1
fi


cleanup() {
    if [ -d "$root_path/logs" ]; then
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Removing Previous Logs..."
        rm -r "$root_path/logs"
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Previous Logs Are Removed!"
    fi
    mkdir "$root_path/logs"
}

cleanup
bash "$root_path/intro.sh"
echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Starting the Channel Detection..."

bash "$root_path/hugepage.sh"

bash "$root_path/build.sh" -t
count=1
while [[ $count -le "$repetition" ]]; do
    new_output_name="${output_name}-${count}.json"
    chrt -f 80 taskset -c 2 stdbuf -oL "$root_path/Blacksmith/build/blacksmith" --dimm-id 1 --ranks 1 --measure-channels --channel-output "$new_output_name"
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        mv "$root_path/$new_output_name" "$root_path/results/$new_output_name"
        ((count++))
    else
        echo -e "${BLACK_TXT}${RED_BG} ThreadHammer ${COLOR_RESET} Detection failed. Retrying iteration $count..."
    fi
    cleanup
done

echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Channel Detection Ended! Thank You for Using ThreadHammer!"
