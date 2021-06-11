#! /bin/bash

set -e

DATE=$(date +%F)
SITES_DIR="/home/www/sites"
BACKUP_DIR="/opt/aws/backup/sites/$DATE"

DATABASES=('db1' 'db2')
SITES=('site1' 'site2')

mount -a

_backup_database() {
    cd /tmp
    mkdir -p $BACKUP_DIR
    local backup_name="$1.backup.sql"
    local archive_name="${BACKUP_DIR}/${backup_name}.tar.gz"

    echo -e "\nBackup database '$1':\n"
    mysqldump --databases $1  > $backup_name
    tar -czvf $archive_name $backup_name
    rm -f $backup_name
}

# Databases backup
if [[ $# > 0 ]]
then
  for db in $@
  do
    if mysql -e "show databases;" | grep -w $db
    then
      _backup_database $db
    else
      echo -e "\nDatabase '$db' is not exist.\n"
    fi
  done
elif [[ $# == 0 ]]
then
  for db in ${DATABASES[@]}
  do
    _backup_database $db
  done

# Sites files backup
mkdir -p $BACKUP_DIR
cd $SITES_DIR
for site in ${SITES[@]}
do
  backup_name="$site.tar.gz"
  archive_name="${BACKUP_DIR}/${site}.tar.gz"

  echo -e "\nBackup site files '$site':\n"
  tar -czf $archive_name "${SITES_DIR}/${site}"

done
fi

echo -e "\nFinish."

