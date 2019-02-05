#!/bin/bash

docker build -t tc-manager:0.1.0 .

docker network create --subnet=172.30.0.0/24 --gateway=172.30.0.254 tcnet
docker run -d --name h1 --net=tcnet --ip 172.30.0.1 --entrypoint=/bin/sh mlabbe/iperf3 -c 'while true; do sleep 100; done'
docker run -d --name h2 --net=tcnet --ip 172.30.0.2 --entrypoint=/bin/sh mlabbe/iperf3 -c 'while true; do sleep 100; done'
INTERFACE1=$(./get_veth_pair.sh h1)
INTERFACE2=$(./get_veth_pair.sh h2)

echo "h1 interface is $INTERFACE1"
echo "h2 interface is $INTERFACE2"
docker run -d --cap-add NET_ADMIN --net=host -v /proc:/proc tc-manager:0.1.0 $INTERFACE1 $INTERFACE2

read -p "Follow instructions of README.md. Press any key to stop and clean."


echo "cleaning"
docker rm -f h1 h2; docker network rm tcnet
