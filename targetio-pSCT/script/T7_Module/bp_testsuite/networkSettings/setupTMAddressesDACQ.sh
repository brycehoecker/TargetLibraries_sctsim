#!/bin/bash

BOARD=$1

echo $BOARD

sshpass -p "" scp -o StrictHostKeyChecking=no authorized_keys root@cta3:.ssh/
sshpass -p "" scp -o StrictHostKeyChecking=no setTMaddresses_dacq1.sh root@cta3: 
sshpass -p "" ssh -o StrictHostKeyChecking=no root@cta3 "/bin/bash /root/setTMaddresses_dacq1.sh"



sshpass -p "" scp -o StrictHostKeyChecking=no authorized_keys root@cta1:.ssh/
sshpass -p "" scp -o StrictHostKeyChecking=no setTMaddresses_dacq2.sh root@cta1: 
sshpass -p "" ssh -o StrictHostKeyChecking=no root@cta1 "/bin/bash /root/setTMaddresses_dacq2.sh"
