import os
import re
from shutil import rmtree

PATH = '/home/www-data'
LINKED_FOLDERS = []
ALL_FOLDERS = []

for f in os.listdir(PATH):

    file_path = os.path.dirname(str(PATH + '/' + f))
    file = file_path + '/' + f

    if os.path.islink(file):
       LINKED_FOLDERS.append(str(os.path.realpath(file)))

    if re.search('^.*[0-9]{10,}$',f):
       ALL_FOLDERS.append(str(file))

all_folders_set    = set(ALL_FOLDERS)
linked_folders_set = set(LINKED_FOLDERS)
difference         = all_folders_set.difference(linked_folders_set)

print('Linked list:')
for i in sorted(LINKED_FOLDERS):
    print(i)

print('Matched list')
for i in sorted(ALL_FOLDERS):
    print(i)

print('Difference (wil be deleted):')
for i in sorted(difference):
    print(i)
    rmtree(i)
