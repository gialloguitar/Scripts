#!/bin/bash
# 
# That script look for all hung fluentd pods on cluster with different envorinment DEV or PROD, redeploy them and delete all old output buffers as only them reach count 33.
# Also, you can use it in CHECK mode for display more information about troubles of fluentd pods with interval 10s. 
#
# Usage:
# SCRIPTNAME <dev|prod> - that command is redeploy all hung fluentd pods and delete all old output buffers.
# SCRIPTNAME <dev|prod> check - that command use for check count of ouput buffers on node
#
# Author: Pereskokov Vladimir


#set -x
trap 'echo "Ctrl-C interrupted bu user..."; exit 1' SIGINT

NOW=$(date +%Y-%m-%d)
TS=$(date +'%H:%M:%S-%d:%m:%Y')
FAULT_COUNT=32
WORKDIR="/opt/eco/scripts/fluentd"
USER="vladimir_pereskokov"
OS_USER="$USER@epam.com"
OS_PASS="*******"
ANSIBLE_DIR="/opt/eco/ansible/inventory-paas"
USAGE="\n
Wrong options \n
\n
Use:\n 
\n
SCRIPTNAME <dev|prod> - that command is redeploy all hung fluentd pods and delete all old output buffers. \n
\n
SCRIPTNAME <dev|prod> check - that command use for check count of output buffers on node\n"
CHECK1="\n 
1. Check for buffer actuality by a current date. Lookup a buffer with a outdate timestamp.
\n"
CHECK2="\n 
2. Lookup stucked pods. If num of output buffer files of fluentd pod greater than $FAULT_COUNT then that pod will consider stucked.
\n"
CHECK3="\n
3. Lookup a Ruby generated SystemError ENOENT - \"No such file or directory\" from fluentd log
Take a last message if exist and compare with a current date.
\n"

cd $ANSIBLE_DIR     # needed for custom ansible.cfg

case "$1" in
new )
# 3.11 Dev
ANSIBLE_INVENTORY="$ANSIBLE_DIR/inventories/hosts-paas-311"
OS_HOST="https://web.paas.epam.com:8443"
LOGGING_PROJ="openshift-logging"
;;
prod )
# 3.9 Prod
ANSIBLE_INVENTORY="$ANSIBLE_DIR/inventories/hosts-paas-39"
OS_HOST="https://console.39.paas.epm-eco.projects.epam.com:8443"
LOGGING_PROJ="logging"
;;
*) 
echo -e $USAGE
exit 0
;;
esac

ANSIBLE_CALL="ansible nodes -u $USER -i $ANSIBLE_INVENTORY -o -m shell -a "

case "$2" in
check )
while true; do
echo -e "\n
Check $1 environment...
\n"

echo -e $CHECK1
$ANSIBLE_CALL"ls -l --time-style=full /var/lib/fluentd/*.log|tail -n1" | awk -v n=$NOW '{if ($13 !~ n && $13 !~ ".*[a-zA-Zа-яА-Я].*|^$") {print "Node " tolower($1) " has too old buffers since " $13}}'

echo -e $CHECK2
$ANSIBLE_CALL"ls /var/lib/fluentd | wc -l " | awk -v f=$FAULT_COUNT '{if ($8 > f && $8 !~ ".*[a-zA-Zа-яА-Я].*|^$") {print "Node " tolower($1) " has " $8 " output buffers"}}'

echo -e $CHECK3
$ANSIBLE_CALL"tail -n3 /var/log/containers/*fluentd* | grep ENOENT" | awk '{if ($3 !~ "FAILED") {print "Node " tolower($1) " has fluentd pod with a ENOENT error"}}'

echo -e "\n========================\n"

sleep 10
done
exit 0
;;
[!^$]*)
echo -e $USAGE
exit 0
;;
esac

os_status=$(oc whoami 2>&1|awk '{print $1}')
os_status_server=$(oc whoami --show-server)

echo -e "======== START - $(date) =====\n"
# Provide valid OpenShift login
if [ $os_status == $OS_USER ]; then 
  if [ $os_status_server != $OS_HOST ]; then 
  oc logout 2> /dev/null
  oc login $OS_HOST -u $OS_USER -p $OS_PASS
  fi
else 
oc login $OS_HOST -u $OS_USER -p $OS_PASS 
fi

oc project $LOGGING_PROJ
os_context=$(oc whoami --show-context)
echo "$TS - $os_context"

# if flunentd output buffers count will reach to 33, it pod will considered is stuck
fault_nodes=( $($ANSIBLE_CALL -o -m shell -a "ls /var/lib/fluentd | wc -l "| \
awk -v f=$FAULT_COUNT '{if($8 > f && $8 !~ ".*[a-zA-Zа-яА-Я].*|^$") { print tolower($1)}}';\
$ANSIBLE_CALL"ls -l --time-style=full /var/lib/fluentd/*.log|tail -n1"| \
awk -v n=$NOW '{if ($13 !~ n && $13 !~ ".*[a-zA-Zа-яА-Я].*|^$") {print tolower($1)}}';\
$ANSIBLE_CALL"tail -n3 /var/log/containers/*fluentd* | grep ENOENT" | awk '{if ($3 !~ "FAILED") {print tolower($1)}}'
) )

count_of_fault_pods=${#fault_nodes[@]}

if [[ $count_of_fault_pods > 0 ]]; then
echo "Num of fault pods is $count_of_fault_pods" 
i=0
for node in ${fault_nodes[@]}; do
  ((i=i+1))
  fault_pod=$(oc adm manage-node --list-pods $node 2>/dev/null | grep fluentd | awk '{print $2}')
  echo "$i) Node $node has a hung fluentd pod $fault_pod"
  # Delete old buffers and hung pods
  oc delete pod $fault_pod --force --grace-period=0
  ssh $USER@$node sudo rm -f /var/lib/fluentd/*
  #echo "Pod $fault_pod was deleted from $node"
done
else
echo "Hung pods was not detected"
fi

echo "=========LOGOUT========"
oc logout
echo "=========FINISH======="

exit 0
