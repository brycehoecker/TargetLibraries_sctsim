import subprocess
import os

# dir=os.system("pwd")
# os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + ':'+'/../Peltier_uC/'


class testPeltier:

    def __init__(self,datadir,report,):

        self.datadir=datadir
        self.report=report

    def executeCmd(self,command):

        output=subprocess.check_output(command+"; exit 0",stderr=subprocess.STDOUT,shell=True)
        try:
            self.outFile.write(output)
            self.outFile.write("------------------------------\n")
        except:
            print "WARNING: output file not defined"
        return output

    def setFuses(self,lfuse=0xff,hfuse=0xd1,efuse=0xfd):

        outp=self.executeCmd("python ../Peltier_uC/AVRcmd.py --w_lfuse {}".format(lfuse))
        outp=self.executeCmd("python ../Peltier_uC/AVRcmd.py --w_hfuse {}".format(hfuse))
        outp=self.executeCmd("python ../Peltier_uC/AVRcmd.py --w_efuse {}".format(efuse))


    def run(self,lfuse=0xff,hfuse=0xd1,efuse=0xfd,setFuses=False):

        self.outFile=open(self.datadir+"Peltier_output.txt","w")

        if setFuses:
            self.setFuses(lfuse=lfuse,hfuse=hfuse,efuse=efuse)
        else:
            pass

        #programming uC
        outp=self.executeCmd("python ../Peltier_uC/cta-avrprog.py -p m328 -U flash:w:../Peltier_uC/hex/PeltierPOST_v5.hex")
        if "Successfully Verified Memory" in outp:
            pass
        else:
            self.report.add_line("FAIL: Peltier uC not programmed correctly")

        #run monitor script
        outp=self.executeCmd("python ../Peltier_uC/Monitor_uC_POST.py")
        if "FAIL" in outp:
            self.report.add_line("FAIL message from Peltier uC monitor script")
        else:
            pass

        blink= raw_input("Is the LED blinking? (blinking rate is slow, ~ 30 s) [Y/N]")
        if blink[0]=='Y':
            pass
        else:
            self.report.add_line("FAIL: LED not blinking")

        self.outFile.close()