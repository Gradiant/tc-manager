#!/bin/bash
# ------------------------------------------------------------------
# [Carlos Giraldo] get veth pair of Docker Container
# ------------------------------------------------------------------

VERSION=0.1.0
USAGE="Usage: get_veth_pair.sh CONTAINER_NAME_OR_ID"

# --- Options processing -------------------------------------------
if [ "$#" -ne 1 ] ; then
    echo $USAGE
    exit 1;
fi

grep -l $(docker exec -i $1 sh -c 'cat /sys/class/net/eth0/iflink') /sys/class/net/veth*/ifindex | grep -Po '(veth[0-9a-z]+)'
