#!/bin/bash

# Applying new servers frokm AH provider
#   1. Change root passwd
#   2. Change ssh port
#   3. Put and run ansible init script
#   4. Set hostname
#   5. Reboot server

set -e

SERVERS=( $(cat new_servers.txt) )
ANSIBLE_INIT_SCRIPT='/Users/markule/Workspace/wisebits/infrastructure/ansible/scripts/init.sh'
PROMPT=''

for IP in ${SERVERS[@]}; do

echo -e "\r\nServer $IP \n"
echo -e "Set connection ssh port:\n"
read -r CON_PORT

SSH_TO="ssh -p$CON_PORT root@"
SCP_TO="scp -P$CON_PORT "

echo -e "# 1. Change root password prompt: Yes/No \n"
read -r PROMPT
if [ $PROMPT == 'Yes' ]; then
NEW_PASS=$(pwgen 16 1 -s)
echo -e "Generated new password (save it): $NEW_PASS \n"
$SSH_TO$IP passwd
else
echo -e "Ignore passwd \r\n"
fi
PROMPT=''

echo -e "Current SSH port from config\n"
$SSH_TO$IP grep Port /etc/ssh/sshd_config

echo -e "# 2. Change ssh port: Yes/No \n"
read -r PROMPT
if [ $PROMPT == 'Yes' ]; then
echo -e "Set SSH port:\n"
read -r SSH_PORT
$SSH_TO$IP sed -i \'s/^Port.*$/Port $SSH_PORT/\' /etc/ssh/sshd_config
echo -e "Port $SSH_PORT have applied to /etc/ssh/sshd_config"
else
echo -e "Ignore change ssh port \r\n"
fi
PROMPT=''

echo -e "# 3. Put and run ansible init script: Yes/No \n"
read -r PROMPT
if [ $PROMPT == 'Yes' ]; then
$SCP_TO $ANSIBLE_INIT_SCRIPT root@$IP:~
$SSH_TO$IP /root/init.sh
else
echo -e "Ignore init.sh \r\n"
fi
PROMPT=''

echo -e "Get current hostname \n"
HOSTNAME=$( $SSH_TO$IP hostname )

echo -e "# 4. Set new hostname promt (curent name: $HOSTNAME): Yes/No \n"
read -r PROMPT
if [ $PROMPT == 'Yes' ]; then
echo -e "New hostname: \n"
read -r HOSTNAME
$SSH_TO$IP hostnamectl set-hostname $HOSTNAME
else
echo -e "Ignore new hostname \r\n"
fi
PROMPT=''

echo -e "# 5. For reboot prompt: Yes/No \n"
read -r PROMPT
if [ $PROMPT == 'Yes' ]; then
echo -e "Server $IP will reboot"
$SSH_TO$IP shutdown --reboot +1
else
echo -e "Ignore reboot \r\n"
fi
PROMPT=''

echo -e "\r\n\n"
done

echo -e "Finish \r\n"
