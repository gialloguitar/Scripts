#!/bin/bash

# Script for Automatic backup virtual drive QCOW2
# Author VladimirP

# current date
DATE=`date +%F`
# y/m/d/h/m separately
YEAR=`date +%Y`
MONTH=`date +%m`
DAY=`date +%d`
HOURS=`date +%H`
MINUTES=`date +%M`

# array of Roman nums 1 to 10
ROMAN=(I II III IV V VI VII VIII IX X)
RINDEX=0

# paths
mount -a       # Mount cifs from fstab
BPATH="/mnt"   # Destination Backup folder
DEFPOOL="/var/lib/libvirt/images"   # Source - Default pool of images
cd $DEFPOOL


IFS=$'\n'
vmlist=( $(virsh list|sed 1,2d|awk '{print $2}') )  # Array with names of running domains
#declare -p vmlist
ACTVMS=${#vmlist[*]}   # Num of running domains


# Completely backup of ALL domains
if [[ $# == 0 ]];then

echo ""
echo "Количество работающих  виртуальных машин: "$ACTVMS
echo ""

for vm in ${vmlist[@]} 
do
 
        echo "=== "${ROMAN[$RINDEX]}" ==="
	echo "Клонируем виртуальный домен: "$vm" ..."
 	
        BDIR="$BPATH/$vm/$vm-$DAY$MONTH$YEAR-$HOURS$MINUTES"
        mkdir --parents $BDIR	
        #vollist=( $(virsh domblklist $vm|sed 1,1d|awk '{print $2}'|sed 's/\/var\/lib\/libvirt\/images\///'))   # used for ALL volumes
		vollist=( $(virsh domblklist $vm|grep qcow2|awk '{print $2}'|sed 's/\/var\/lib\/libvirt\/images\///'))  # used for only QCOW2
        #declare -p vollist
              for vol in ${vollist[@]}
	      do
                clonevol="clone-$vol"
	        virsh vol-clone $vol $clonevol --pool default
		mv $clonevol $BDIR/$vol
	      done
        vollist=()
        virsh pool-refresh default
        
	echo "XML-дамп машины: "$vm".xml"
	virsh dumpxml $vm > $BDIR/$vm.xml
	RINDEX=$((++RINDEX))
done

# Backup given domains, need separated by space 
elif [[ $# > 0 ]];then
      
      for vm in $@;do
          if [[ "${vmlist[*]}" == *"$vm"* ]];then
	       
	       echo "=== "${ROMAN[$RINDEX]}" ===" 
	       echo "Клонируем виртуальный домен: "$vm" ..."
	  
                     BDIR="$BPATH/$vm/$vm-$DAY$MONTH$YEAR-$HOURS$MINUTES"
                     mkdir --parents $BDIR	
                     #vollist=( $(virsh domblklist $vm|sed 1,1d|awk '{print $2}'|sed 's/\/var\/lib\/libvirt\/images\///'))   # used for ALL volumes
		             vollist=( $(virsh domblklist $vm|grep qcow2|awk '{print $2}'|sed 's/\/var\/lib\/libvirt\/images\///'))  # used for only QCOW2
                     #declare -p vollist
                        for vol in ${vollist[@]}
	                   do
                           clonevol="clone-$vol"
	                   virsh vol-clone $vol $clonevol --pool default
		           mv $clonevol $BDIR/$vol
	                   done
                           vollist=()
                           virsh pool-refresh default
        
	        echo "XML-дамп машины: "$vm".xml"
	        virsh dumpxml $vm > $BDIR/$vm.xml
	        RINDEX=$((++RINDEX))
	  else
               echo "====!!!===="
	       echo "Домен "$vm" не обнаружен!"
	       echo "1. проверьте запущен ли домен"
	       echo "2. убедитесь в правильности написания имени домена "$vm
	       echo ""
	  fi  
      done

fi

chown -R super:super $BPATH  # change user:group on storage for accessibility in them, better make it by UID:GID according remote passwd

echo "==="
echo "Завершено"

exit 0

