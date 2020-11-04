#!/bin/bash

set -o pipefail

cd /home/www-data

BUILD_STRIPCASH=$(ls -l stripcash.com | cut -d '>' -f2 | egrep -o '[0-9]{10,}')
BUILD_API_STRIPCASH=$(ls -l api.stripcash.com | cut -d '>' -f2 | egrep -o '[0-9]{10,}')


rm -rf $(ls -1 | grep '^stripcash\.com\.[0-9].*$' | grep -v ${BUILD_STRIPCASH} )
rm -rf $(ls -1 | grep '^api.stripcash\.com\.[0-9].*$' | grep -v ${BUILD_API_STRIPCASH} )