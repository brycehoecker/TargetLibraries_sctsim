#!/bin/bash
#
# Author:	Thomas Meures
# Date:		22 March 2017
# Version:	v0.0
# Description:	Control main switch of Wiener power supply
#


STATE=$1
snmpset -v 2c -m $CTA_CONTROL_DIR/powerControl/WIENER-CRATE-MIB-2.txt -c guru 172.16.55.74 sysMainSwitch.0 i $STATE
 
