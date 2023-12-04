#!/bin/bash

ifconfig eth0 192.168.10.1
ifconfig eth1 192.168.12.1

arp -s 192.168.10.2 02:34:56:78:9b:00
arp -s 192.168.12.2 02:34:56:78:9b:01

###DACQ1
arp -s 192.168.10.36 08:00:56:00:03:24   ##FEE112
arp -s 192.168.10.157 08:00:56:00:03:9d   ##FEE114
arp -s 192.168.10.109 08:00:56:00:03:6d   ##FEE123
arp -s 192.168.10.114 08:00:56:00:03:72   ##FEE124
arp -s 192.168.10.131 08:00:56:00:03:83   ##FEE128
arp -s 192.168.10.81 08:00:56:00:03:51    ##FEE100
arp -s 192.168.12.64 08:00:56:00:03:40    ##FEE107
arp -s 192.168.12.180 08:00:56:00:03:b4   ##FEE108
arp -s 192.168.12.127 08:00:56:00:03:7f   ##FEE111
arp -s 192.168.12.247 08:00:56:00:03:f7   ##FEE116 and FEE115
arp -s 192.168.12.229 08:00:56:00:03:e5   ##FEE121
arp -s 192.168.12.45 08:00:56:00:03:2d    ##FEE118
arp -s 192.168.12.130 08:00:56:00:03:82   ##FEE119

###DACQ2
arp -s 192.168.11.122 08:00:56:00:03:7a   ##FEE125
arp -s 192.168.11.188 08:00:56:00:03:bc   ##FEE126
arp -s 192.168.11.89 08:00:56:00:03:59    ##FEE101
arp -s 192.168.11.101 08:00:56:00:03:65   ##FEE110
