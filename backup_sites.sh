#! /bin/bash
####Срипт работает в кроне, базы и саты для бэкапа перечислены в массиве DBASES и SITES соответственно
####так же срипт можно запускать вручную, через пробел указав необходимые базы (каталоги бэкапятся только в кроне).
####Бэкапы  сжаты Гзипом и лежат на сервере

# current date
DATE=`date +%F`
# y/m/d/h/m separately
YEAR=`date +%Y`
MONTH=`date +%m`
DAY=`date +%d`
HOURS=`date +%H`
MINUTES=`date +%M`
#DB credentials
DBUSER="*****"
DBPASS="*****"
DBHOST="localhost"
#databases and sites for backup
DBASES=('social_st' 'social_pr')  #
SITES=('social')
#mount path
MPATH="/media/"

mysql -h $DBHOST -u $DBUSER -p$DBPASS -e "show databases;" > /opt/bases_tmp
sed 1,1d /opt/bases_tmp > /opt/bases
rm /opt/bases_tmp
#BASELIST=`cat /opt/bases`

#Paths

#/sbin/mount.cifs //192.168.000.000/d$/backup/ubuntu "$MPATH" -o user=super,password=$DBPASS,domain=DOM
mount -a       # Все пути лучше из fstab монтировать
BACKUP_DIR="$MPATH/BackupSites/$YEAR-$MONTH-$DAY/Time-$HOURS-$MINUTES"
mkdir --parents $BACKUP_DIR
cd $BACKUP_DIR

if [[ $# > 0 ]];then
echo "Бэкап $# баз данных вручную:"
             for i in $@;do
                      if grep -w $i /opt/bases;then
backup_name="$YEAR-$MONTH-$DAY.$HOURS-$MINUTES.$i.backup.sql"
backup_tarball_name="$backup_name.tar.gz"
echo "Dump of $i"
mysqldump -h "$DBHOST" --databases "$i" -u "$DBUSER" --password="$DBPASS" > "$backup_name"
echo "Compress..."
tar -zcf "$backup_tarball_name" "$backup_name"
rm "$backup_name"
echo "Done."
echo
                     else
                        echo "База данных $i не обнаружена, проверьте написание!"
                        echo
                     fi
            done
      elif [[ $# == 0 ]];then
            for database in ${DBASES[@]};do
backup_name="$YEAR-$MONTH-$DAY.$HOURS-$MINUTES.$database.backup.sql"
backup_tarball_name="$backup_name.tar.gz"
mysqldump -h "$DBHOST" --databases "$database" -u "$DBUSER" --password="$DBPASS" > "$backup_name"
tar -zcf "$backup_tarball_name" "$backup_name"
rm "$backup_name"
            done
#####Архивация каталогов сайтов
mkdir sites
cd sites
       for j in ${SITES[@]};do
tar -zcf "$YEAR-$MONTH-$DAY.$HOURS-$MINUTES.$j.tar.gz" "/home/$j"
       done
fi
#cd ~
umount -l "$MPATH"
