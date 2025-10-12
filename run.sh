#!/bin/bash

source conf.cfg
root_path=$ROOT_PATH

rm -rf "$root_path/results"
mkdir "$root_path/results"
mkdir -p "$root_path/logs"
header_file="$root_path/Blacksmith/include/GlobalDefines.hpp"
runtime_file="$root_path/results/runtime_data.txt"
iteration_runtime_file="$root_path/results/runtime_data_iterations.txt"

start_epoch_initial=$(date +%s)
start_date=$(TZ=Europe/Berlin date '+%d.%m.%Y %H:%M:%S %Z')

{
  echo "START_EPOCH=${start_epoch_initial}"
  echo "START_CEU=${start_date}"
} > "$runtime_file"

MAX_SWEEP_SIZE=$(grep -E '^#define[[:space:]]+MAX_SWEEP_SIZE' "$header_file" | awk '{print $3}')
active_threads=$(nproc)
SWEEP_CHUNK=$(( MAX_SWEEP_SIZE / N_THREADS ))

# Read json file && || Set Repetition
pattern_json_path=""
pattern_path=""
repetition=1
while getopts "j:r:p:m" opt; do
  case $opt in
    j) pattern_json_path="$OPTARG" ;;
    p) pattern_path="$OPTARG" ;;
    r) repetition="$OPTARG" ;;
    m) multi_thread=true ;;
    \?) echo "Usage: $0 [-j json_file] [-p Path to pattern json files] [-m multi-thread (-j flag must be present)] [-r repetition] [Default: Original Blacksmith Fuzzing]"; exit 1 ;;
  esac
done
shift $((OPTIND -1))

if [[ -n "$multi_thread" ]]; then
    if [[ -z "$pattern_path" ]]; then
        echo -e "${BLACK_TXT}${RED_BG} ThreadHammer ${COLOR_RESET} [-p] Flag is missing! Please set the patterns path."
        exit 1
    fi
    sweeping_single=false
    sweeping_multi=true
elif [[ -n "$pattern_json_path" ]]; then
    sweeping_single=true
    sweeping_multi=false
else
    sweeping_single=false 
    sweeping_multi=false
fi

cleanup() {
    if [ -d "$root_path/logs" ]; then
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Removing Previous Logs..."
        rm -rf "$root_path/logs"
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Previous Logs Are Removed!"
    fi
    mkdir "$root_path/logs"
}

compress() {
    bash "$root_path/compress.sh"
}

log_info(){
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Starting the Experiment..."
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} REPITITION = ${repetition}"
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} ACTIVE THREADS = ${active_threads}"
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} N_THREADS = ${N_THREADS}"
}

cleanup

bash "$root_path/intro.sh"

bash "$root_path/hugepage.sh"

if [[ "$sweeping_single" == "true" ]]; then
    bash "$root_path/build.sh" -t
    log_info
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} SWEEP_AREA = ${MAX_SWEEP_SIZE}MiB"
    count=1
    while [[ $count -le "$repetition" ]]; do
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} TRYING ITERATION ${count}"
        start_epoch=$(date +%s)
        start_date=$(TZ=Europe/Berlin date '+%d.%m.%Y %H:%M:%S %Z')
        {
            echo "/////////////////////// ITERATION ${count} ///////////////////////"
            echo "START_EPOCH=${start_epoch}"
            echo "START_CEU=${start_date}"
        } >> "$runtime_file"

        output_name="sweeping-result${count}.json"
        stdbuf -oL "$root_path/Blacksmith/build/blacksmith" --dimm-id 1 --ranks 1 --load-json "$pattern_json_path" --sweeping 
        exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            mv "$root_path/sweep-summary-1x${MAX_SWEEP_SIZE}MB.json" "$root_path/results/$output_name"
            end_epoch_iteration=$(date +%s)
            end_date_iteration=$(TZ=Europe/Berlin date '+%d.%m.%Y %H:%M:%S %Z')
            duration_iteration=$((end_epoch_iteration - start_epoch))
            hours=$((duration_iteration / 3600))
            minutes=$(((duration_iteration % 3600) / 60))
            seconds=$((duration_iteration % 60))
            {
                echo "END_EPOCH=${end_epoch_iteration}"
                echo "END_CEU=${end_date_iteration}"
                echo "DURATION_SEC=${duration_iteration}"
                printf "DURATION_HMS=%02d:%02d:%02d\n" $hours $minutes $seconds
                echo "//////////////////////////////////////////////////////////"
            } >> "$runtime_file"
            ((count++))
        else
            echo -e "${BLACK_TXT}${RED_BG} ThreadHammer ${COLOR_RESET} Blacksmith failed. Retrying iteration $count..."
        fi
    done
elif [[ "$sweeping_multi" == "true" ]]; then
    bash "$root_path/build.sh" -t
    log_info
    echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} SWEEP_AREA = ${SWEEP_CHUNK}MiB"
    count=1
    while [[ $count -le "$repetition" ]]; do
        echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} TRYING ITERATION ${count}"
        stdbuf -oL "$root_path/Blacksmith/build/blacksmith" --dimm-id 1 --ranks 1 --pattern-path "$pattern_path" --multi-threading --sweeping 
        exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            mkdir -p "$root_path/results/rep${count}"
            shopt -s nullglob
            for f in "$root_path"/*.json; do
                mv -n -- "$f" "$root_path/results/rep${count}"
            done
            shopt -u nullglob
            ((count++))
        else
            echo -e "${BLACK_TXT}${RED_BG} ThreadHammer ${COLOR_RESET} Blacksmith failed. Retrying iteration $count..."
        fi
    done
else
    bash "$root_path/build.sh"
    stdbuf -oL "$root_path/Blacksmith-Original/build/blacksmith" --dimm-id 1 --runtime-limit "$DEFAULT_RUNTIME" --ranks 1
    compress
fi

end_epoch=$(date +%s)
end_date=$(TZ=Europe/Berlin date '+%d.%m.%Y %H:%M:%S %Z')

duration=$((end_epoch - start_epoch_initial))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))
{
  echo "END_EPOCH=${end_epoch}"
  echo "END_CEU=${end_date}"
  echo "DURATION_SEC=${duration}"
  printf "DURATION_HMS=%02d:%02d:%02d\n" $hours $minutes $seconds
} >> "$runtime_file"


echo -e "${BLACK_TXT}${PURPLE_BG} ThreadHammer ${COLOR_RESET} Experiment Ended! Thank You for Using ThreadHammer!"
