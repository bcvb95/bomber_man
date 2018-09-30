#!/usr/bin/env bash

python bomberman.py --username Baba1 --client_port 30000 --serv_ip 192.168.1.105 --serv_port 30004 --is_server & 
sleep 5s
python bomberman.py --username Baba2 --client_port 30001 --serv_ip 192.168.1.105 --serv_port 30004 &
#sleep 2s
#python bomberman.py --username Baba3 --client_port 30002 --serv_ip 192.168.1.105 --serv_port 30004 &
#sleep 2s
#python bomberman.py --username Baba4 --client_port 30003 --serv_ip 192.168.1.105 --serv_port 30004 &