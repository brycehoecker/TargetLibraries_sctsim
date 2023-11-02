if [ "$#" -ne 2 ]; then
    echo "usage: $0 amplitude(Volts) freqency(Hz) "
    echo "example: for 1 V, 1 kHz frequency"
    echo "$0 1 1000"
    exit
fi

outdev=/dev/ttyS0

stty -F ${outdev} 115200

peak=$1
freq=$2
ampl=`awk -v a=${peak} 'BEGIN{printf "%.5f", a}'`
offs=`awk -v a=${peak} 'BEGIN{printf "%.5f", a/2}'`

echo freq = ${freq}

echo "selected frequency: ${freq} Hz"
echo "selected amplitude ${ampl} V"
#echo "offset ${offs}"

echo "OUTPUT OFF" > ${outdev} #turn off output while changing settings
echo "OUTPUT:POLARITY NORMAL" > ${outdev}
echo "FUNC PULSE" > ${outdev}
echo "PULSE:WIDTH 8e-9" > ${outdev} #minimum width is 8 ns
echo "PULSE:TRANSITION 5e-9" > ${outdev} #minimum edge is 5 ns, max 1 ms, limits: Edge Time < 0.625 X Pulse Width
echo "BURS:STAT OFF" > ${outdev} #disable burst
echo "FREQ ${freq}" > ${outdev}
echo "VOLT ${ampl}" > ${outdev}
echo "VOLT:OFFS ${offs}" > ${outdev}
echo "*WAI" > ${outdev} #wait for all operation to complete (just in case)
echo "OUTPUT ON" > ${outdev}
#read -p "Press enter to turn the output off"
#echo "OUTPUT OFF" > ${outdev}


