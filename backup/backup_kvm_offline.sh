#!/bin/bash

set -e

DATE=$(date +%F)
BACKUP_DIR="/opt/aws/backup/kvm/$DATE"
BACKUP_TTL=30

_backup_vm() {
  local vm=$1
  local volume=$2
  local volume_name=$(grep -o '[^/]*.qcow2' <<< $2)
  local pool=$3

  echo "Clone ${volume_name}..."

  mkdir -p "${BACKUP_DIR}/${vm}"
  virsh vol-clone --pool $pool "$volume" "${volume_name}.back"
  cp -f "${volume}.back" "${BACKUP_DIR}/${vm}/${volume_name}"
  rm -f "${volume}.back"
  virsh pool-refresh $pool

  echo "Dump XML of domain ${vm}..."
  virsh dumpxml $vm > "${BACKUP_DIR}/${vm}/${vm}.xml"
  echo "Done."
}

mount -a

if [[ $# == 0 ]]
then

for domain in $(virsh list --state-running --name | sed '/^$/d')
do
  echo "Gracefully shutdown a domain ${domain}"
  virsh shutdown $domain
  sleep 30

  for volume in $(virsh domblklist $domain | grep qcow2 | awk '{print $2}')
  do
    case "$volume" in
    */var/lib/libvirt/images/*)
      _backup_vm "$domain" "$volume" default
    ;;
    */opt/storage/images/*)
      _backup_vm "$domain" "$volume" images
    ;;
    esac
  done

  echo "Start domain ${domain}"
  virsh start $domain

done

elif [[ $# == 1 ]]
then
  domain=$1
  echo "Gracefully shutdown a domain ${domain}"
  virsh shutdown $domain
  sleep 30

  for volume in $(virsh domblklist $domain | grep qcow2 | awk '{print $2}')
  do
    case "$volume" in
    */var/lib/libvirt/images/*)
      _backup_vm "$domain" "$volume" default
    ;;
    */opt/storage/images/*)
      _backup_vm "$domain" "$volume" images
    ;;
    esac
  done

  echo "Start domain ${domain}"
  virsh start $domain
fi

echo -e "\nDelete backups older ${BACKUP_TTL} days:\n"
find /opt/aws/backup/kvm -type d -mtime +${BACKUP_TTL} -exec rm -rf "{}" \;

echo "Finish"

