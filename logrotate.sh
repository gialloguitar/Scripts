#!/bin/bash
set -e

usage="\n
Script will be compress and cleanup all matched logs according on Hot -h and Cold -c limits. Default suffix .tar.gz will be appended to all compressed files.\n
Specify a log pattern with a key -l like '/var/log/messages*' (quotes is necessary)\n\n
Additional features:
-l - Logs pattern like '/home/logs/*.log' or '/var/log/messages'\n
-h - A time to keep uncompressed logs in days (default: 7) as a Hot limit\n
-c - A time to keep old compressed logs in months (default: 12) as a Cold limit\n
-o - Owner of new compressed files (default: root)\n
-g - Group of new compressed files (default: root)\n\n
Example:
logrotate.sh -l '/home/logs/*.log' -o www-data -g www-data -h 7 -c 24
\n"

current_epoch=$(date +%s)
suffix='.tar.gz'
def_owner='root'
def_group='root'
def_months='12'
def_days='7'

while getopts l:h:c:o:g: flag
do
    case "${flag}" in
        l) logs=${OPTARG}
           ;;
        h) hot_limit=${OPTARG}
           ;;
        c) cold_limit=${OPTARG}
           ;;
        o) owner=${OPTARG}
           ;;
        g) group=${OPTARG}
           ;;
        *) echo -e $usage
           exit 0
           ;;
    esac
done

_threshold_month() {
    local day_in_sec=86400
    local days_in_month=30
    local months_in_sec=$(( $1*${days_in_month}*${day_in_sec} ))
    local delta=$(( ${current_epoch}-${months_in_sec} ))
    echo $delta
}

_threshold_days() {
    local day_in_sec=86400
    local days_in_sec=$(( $1*${day_in_sec} ))
    local delta=$(( ${current_epoch}-${days_in_sec} ))
    echo $delta
}

echo -e "Run logrotation: $(date)\n"

# # Compress files
echo -e "Compress logs older ${hot_limit:-$def_days} days\n"
hot_threshold=$(_threshold_days ${hot_limit:-$def_days})
for log in $(ls -1 ${logs})
do
    mtime=$(stat -c %Y ${log} | awk '{print $1}')
    if [[ $mtime < $hot_threshold ]]
    then
        echo "Will be rotate: $log"
        tar --remove-files -cvzf ${log}${suffix} ${log}
        chown ${owner:-$def_owner}:${group:-$def_group} ${log}${suffix}
    fi
done

# Remove old files
echo -e "Removing compressed logs older ${cold_limit:-$def_months} months\n"
cold_threshold=$(_threshold_month ${cold_limit:-$def_months})
archives=$(echo ${logs}${suffix})
for f in $(ls -1 ${archives})
do
    mtime=$(stat -c %Y $f | awk '{print $1}')
    if [[ $mtime < $cold_threshold ]]
    then
        echo "Will be removing: $f"
        rm -f $f
    fi
done
