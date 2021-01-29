#!/bin/bash
set -e

usage="\n
Script will be compress and cleanup all matched logs according on Hot -h and Cold -c limits. Default SUFFIX .tar.gz will be appended to all compressed files.\n
Specify a log pattern with a key -l like '/var/log/messages*' (quotes is necessary)\n\n
Additional features:\n
-l - Logs pattern like '/home/logs/*.log' or '/var/log/messages'\n
-h - A time to keep uncompressed logs in days (default: 7) as a Hot limit\n
-c - A time to keep old compressed logs in months (default: 12) as a Cold limit\n
-o - Owner of new compressed files (default: root)\n
-g - Group of new compressed files (default: root)\n
-d - Dry-run mode (default: false)\n
-m - Moving archives to dir. Folder for placing of all compressed Cold logs, by default store comressed logs in same folder as logs (default: false)\n
-s - IP or DNS of NFS server. To form valid remoted mount pont use with  -r option. It will be use command 'mount -t nfs <IP>:<REMOVING_DIR> /tmp/<TEMPORARY_MOUNTED_DIR>'\n
\n
Example:
logrotate.sh -l '/home/logs/*.log' -o www-data -g www-data -h 7 -c 24 -d true -m '/backup/logs' -s '192.168.0.1'
\n
\n"

CURRENT_EPOCH=$(date +%s)
SUFFIX='.tar.gz'
DEF_OWNER='root'
DEF_GROUP='root'
DEF_MONTHS='12'
DEF_DAYS='7'
DEBUG=false
SERVER=
MOVE_TO_DIR=
HOSTNAME=
TMP_MOUNT_POINT="/tmp/comressed_logs_$CURRENT_EPOCH"

while getopts l:h:c:o:g:d:m:s: flag
do
    case "${flag}" in
        l) LOGS=${OPTARG}
           ;;
        h) HOT_LIMIT=${OPTARG}
           ;;
        c) COLD_LIMIT=${OPTARG}
           ;;
        o) OWNER=${OPTARG}
           ;;
        g) GROUP=${OPTARG}
           ;;
        d) DEBUG=${OPTARG}
           ;;
        m) MOVE_TO_DIR=${OPTARG}
           ;;
        s) SERVER=${OPTARG}
           ;;
        *) echo -e $usage
           exit 1
           ;;
    esac
done

DIRNAME="$(dirname "$LOGS")/"

_threshold_month() {
    local day_in_sec=86400
    local days_in_month=30
    local months_in_sec=$(( $1*${days_in_month}*${day_in_sec} ))
    local delta=$(( ${CURRENT_EPOCH}-${months_in_sec} ))
    echo $delta
}

_threshold_days() {
    local day_in_sec=86400
    local days_in_sec=$(( $1*${day_in_sec} ))
    local delta=$(( ${CURRENT_EPOCH}-${days_in_sec} ))
    echo $delta
}

case $DEBUG in
  false|true) echo -e "DEBUG mode: $DEBUG\n"
    ;;
  *) echo -e $usage
     exit 1
    ;;
esac

if [[ ! -z $MOVE_TO_DIR ]] && [[ -z $SERVER ]]
then
    case $MOVE_TO_DIR in
        /*) MOVE_TO_DIR="$MOVE_TO_DIR/"
            ;;
        */) MOVE_TO_DIR="$(dirname $MOVE_TO_DIR)$MOVE_TO_DIR"
            ;;
        *) MOVE_TO_DIR="$(dirname $MOVE_TO_DIR)/$MOVE_TO_DIR/"
            ;;
    esac

    if [[ ! -d $MOVE_TO_DIR ]]
    then
        echo -e "\nWarning!\nDirectory is not exist: $MOVE_TO_DIR\n\n"
        echo -e  $usage
        exit 1
    fi
    DIRNAME=${MOVE_TO_DIR}
fi

if [[ ! -z $SERVER ]]
then
    if [[ -z $MOVE_TO_DIR ]]
    then
       echo -e "\nWarning!\nNeed to specify remote dir with a '-m' option for forming of NFS mount point\n\n"
       exit 1
    fi
    echo "Mount remote folder ${SERVER}:${MOVE_TO_DIR}"
    mkdir -p ${TMP_MOUNT_POINT}
    mount.nfs -v ${SERVER}:${MOVE_TO_DIR}  ${TMP_MOUNT_POINT}
    mkdir -p ${TMP_MOUNT_POINT}
    DIRNAME="${TMP_MOUNT_POINT}/"
fi

echo -e "\nRun logrotation: $(date)"

echo -e "\nCompress logs older ${HOT_LIMIT:-$DEF_DAYS} days\n"
hot_threshold=$(_threshold_days ${HOT_LIMIT:-$DEF_DAYS})
for log in $(ls -1 ${LOGS})
do
    mtime=$(stat -c %Y ${log} | awk '{print $1}')
    if [[ $mtime < $hot_threshold ]]
    then
        echo "Will be rotate: $log"
        if [[ $DEBUG == 'false' ]]
        then
            tar --remove-files -cvzf ${log}${SUFFIX} ${log}
            chown ${OWNER:-$DEF_OWNER}:${GROUP:-$DEF_GROUP} ${log}${SUFFIX}
        else
            echo "tar --remove-files -cvzf ${log}${SUFFIX} ${log}"
            echo "chown ${OWNER:-$DEF_OWNER}:${GROUP:-$DEF_GROUP} ${log}${SUFFIX}"
        fi
    fi
done

if [[ ! -z $MOVE_TO_DIR ]] || [[ -z $SERVER ]]
then
    echo -e "\nMove archives to: $DIRNAME"
    if [[ $DEBUG == 'false' ]]
    then
        rsync -avz --remove-source-files ${LOGS}${SUFFIX} ${DIRNAME}
    else
        echo "rsync -avz --remove-source-files ${LOGS}${SUFFIX} ${DIRNAME}"
    fi
fi

echo -e "\nRemoving compressed logs older ${COLD_LIMIT:-$DEF_MONTHS} months\n"
cold_threshold=$(_threshold_month ${COLD_LIMIT:-$DEF_MONTHS})
archives=$(echo ${DIRNAME}$(basename "${LOGS}")${SUFFIX})
for file in $(ls -1 ${archives})
do
    mtime=$(stat -c %Y $file | awk '{print $1}')
    if [[ $mtime < $cold_threshold ]]
    then
        echo "Will be removing: $file"
        if [[ $DEBUG == 'false' ]]
        then rm -f $file
        else echo "rm -f $file"
        fi
    fi
done

if [[ ! -z $SERVER ]] && [[ ! -z $MOVE_TO_DIR ]]
then
    umount ${TMP_MOUNT_POINT}
    rm -rf ${TMP_MOUNT_POINT}
fi

echo -e "\nFinish logrotation: $(date)\n"
