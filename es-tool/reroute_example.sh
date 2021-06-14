/bin/bash

set -xe

SHARD=1
NODE=sc-es-05

DANGLING_INDICES=$(curl -s localhost:9200/_cat/shards?h=index,shard,prirep,state,unassigned.reason,node | grep DANGLING | awk '{print $1}' | sort -h | uniq)

for i in $DANGLING_INDICES
do

_data()
{
  cat <<EOF
{"commands": [{
        "allocate_stale_primary": {
            "index": "$i",
            "shard": $SHARD,
            "node": "$NODE",
            "accept_data_loss": true
     }
  }]
}
EOF
}


_data·

curl -s -D- http://127.0.0.1:9200/_cluster/reroute -H "Content-Type: application/json" -d "$(_date)"

done

