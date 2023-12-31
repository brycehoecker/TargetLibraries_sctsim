#!/bin/bash

##ifconfig eth0 192.168.10.1
##ifconfig eth0 mtu 9000
##sleep 1
##ifconfig eth1 192.168.12.1
##ifconfig eth1 mtu 9000
##sleep 1
##ifconfig eth4 192.168.13.1
##ifconfig eth4 mtu 9000
##sleep 1


arp -s 192.168.10.2 02:34:56:78:9b:00  ##DACQ1, wr0
arp -s 192.168.12.2 A6:76:1D:39:80:EC  ##DACQ2, wr0
arp -s 192.168.13.2 A6:76:1D:39:80:ED  ##DACQ2, wr1
arp -s 192.168.14.2 02:34:56:78:9B:01  ##DACQ1, wr1
###arp -s 192.168.10.3 02:34:56:78:9B:01

###DACQ1
arp -s 192.168.10.109 08:00:56:00:03:6d   ##FEE123
#arp -s 192.168.10.131 08:00:56:00:03:83   ##FEE128
arp -s 192.168.10.247 08:00:56:00:03:f7   ##FEE115
arp -s 192.168.10.180 08:00:56:00:03:b4   ##FEE108
arp -s 192.168.10.229 08:00:56:00:03:e5   ##FEE121
arp -s 192.168.10.45 08:00:56:00:03:2d    ##FEE118
arp -s 192.168.10.130 08:00:56:00:03:82   ##FEE119

arp -s 192.168.14.127 08:00:56:00:03:7f   ##FEE111
arp -s 192.168.14.64 08:00:56:00:03:40    ##FEE107
arp -s 192.168.14.81 08:00:56:00:03:51    ##FEE100
arp -s 192.168.14.114 08:00:56:00:03:72   ##FEE124
arp -s 192.168.14.157 08:00:56:00:03:9d   ##FEE114
arp -s 192.168.14.36 08:00:56:00:03:24   ##FEE112


###DACQ2
arp -s 192.168.12.122 08:00:56:00:03:7a   ##FEE125
arp -s 192.168.12.188 08:00:56:00:03:bc   ##FEE126
#arp -s 192.168.12.89 08:00:56:00:03:59    ##FEE101
arp -s 192.168.12.202 08:00:56:00:03:ca   ##FEE 106 (replaces 101)
arp -s 192.168.12.101 08:00:56:00:03:65   ##FEE110
arp -s 192.168.12.22 08:00:56:00:03:16   ##FEE1 from Italy
arp -s 192.168.12.191 08:00:56:00:03:bf   ##FEE4 from Italy
arp -s 192.168.12.98 08:00:56:00:03:62   ##FEE3 from Italy
arp -s 192.168.12.82 08:00:56:00:03:52   ##FEE9 from Italy
arp -s 192.168.12.105 08:00:56:00:03:69   ##FEE6 from Italy
arp -s 192.168.12.76 08:00:56:00:03:4c   ##FEE2 from Italy
