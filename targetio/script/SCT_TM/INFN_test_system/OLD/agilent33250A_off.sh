outdev=/dev/ttyS0

stty -F ${outdev} 115200

echo "OUTPUT OFF" > ${outdev} #turn off output while changing settings
