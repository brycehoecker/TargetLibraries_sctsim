# Brent Mode
# Created 16 July 2019 to control Agilent33600A waveform generator.

import sys
import visa
import time

class Agilent33600A(object):
    def __init__(self):
        self.status = True
        self.rm = visa.ResourceManager()
        #resource = 'USB0::0x0957::0x4B07::MY53400322::0::INSTR'
        resource = 'USB0::2391::19207::MY53400322::0::INSTR'
        self.instrument = self.rm.open_resource(resource)
        print(self.instrument.query("*IDN?"))
        print("Agilent 33600A function generator connected successfully!")

    def apply_pulse(self, freq, ampl, offset, width):
        """Function generator takes amplitude and sets half height above 0 and half below. So the behavior planned for here is under the expectation that what is really desired is to specify the amplitude and offset as a height above 0. Thus, if you specify that the offset is 0, the baseline of the pulse will indeed rest at 0. Be careful with this!"""
        if (ampl > 5.0) or (ampl + offset > 5.0) or (-1.0 * ampl - offset < -5.0):
            print("WARNING: These pulse settings could damage the module. Try something else!")
            raise SystemExit
        else:
            self.instrument.write("SOURce1:FUNCtion PULS")
            self.instrument.write("SOURce1:VOLTage {}".format(ampl))
            self.instrument.write("SOURce1:FREQuency {}".format(freq*10))
            self.instrument.write("SOURce1:VOLTage:OFFSet {}".format(ampl/2))
            #self.instrument.write("SOURce1::PULS: {},{},{}".format(freq, ampl, (ampl/2 + offset)))
            #self.instrument.write("SOURce1:APPL:PULS {},{},{}".format(freq, ampl, (ampl/2 + offset)))
            self.instrument.write("SOURce1:PULS:WIDTH {}e-9".format(width))
            self.instrument.write("SOURce1:BURSt:STATe ON")
            self.instrument.write("SOURce1:BURSt:INTernal:PERiod {}".format(1.0/freq))
		
            self.instrument.write("SOURce1:FUNCtion:ARBitrary:SYNChronize")

            self.instrument.write("OUTPut1 ON")
            print("Outputting pulse now.")


    def apply_trigger_pulse(self, freq, ampl, offset, width):
        """This function has Source2 hardcoded as pulse output to make sure it does not go anywhere else. Function generator takes amplitude and sets half height above 0 and half below. So the behavior planned for here is under the expectation that what is really desired is to specify the amplitude and offset as a height above 0. Thus, if you specify that the offset is 0, the baseline of the pulse will indeed rest at 0. Be careful with this!"""
        if (ampl > 3.3) or (ampl + offset > 3.3) or (-1.0 * ampl - offset < -3.3):
            print("WARNING: These pulse settings could damage the module. Try something else!")
            raise SystemExit
        else:
            self.instrument.write("SOURce2:FUNCtion PULS")
            self.instrument.write("SOURce2:VOLTage {}".format(ampl))
            self.instrument.write("SOURce2:FREQuency {}".format(freq*10))
            self.instrument.write("SOURce2:VOLTage:OFFSet {}".format(ampl/2))
            self.instrument.write("SOURce2:PULS:WIDTH {}e-9".format(width))
            self.instrument.write("SOURce2:BURSt:STATe ON")
            self.instrument.write("SOURce2:BURSt:INTernal:PERiod {}".format(1.0/freq))
            self.instrument.write("SOURce2:FUNCtion:ARBitrary:SYNChronize")
            
	    self.instrument.write("OUTPut2 ON")
            
            print("Outputting pulse now.")




    def apply_sin(self, freq, ampl, offset):
        if (ampl > 4.0) or (ampl + offset > 4.0) or (-1.0 * ampl - offset < -4.0):
            print("WARNING: These sinusoid settings could damage the module. Try something else!")
            raise SystemExit
        else:
	    self.instrument.write("SOURce1:BURSt:STATe OFF")
	    self.instrument.write("SOURce1:FUNCtion SIN")
	    self.instrument.write("SOURce1:VOLTage {}".format(ampl))
	    self.instrument.write("SOURce1:VOLTage:OFFSet {}".format(0))
	    self.instrument.write("SOURce1:FREQuency {}".format(10e6))
	    self.instrument.write("OUTPut1 ON")
            #self.instrument.write("APPL:SIN {},{},{}".format(freq, ampl, offset))
            print("Outputting sin now.")

    def apply_noise(self, ampl, offset):
        if (ampl > 0.1) or (ampl + offset > 0.1) or (-1.0 * ampl - offset < -0.1):
            print("WARNING: These sinusoid settings could damage the module. Try something else!")
            raise SystemExit
        else:
	    self.instrument.write("SOURce1:BURSt:STATe OFF")
	    self.instrument.write("SOURce1:FUNCtion NOISe")
	    self.instrument.write("SOURce1:VOLTage {}".format(ampl))
	    self.instrument.write("SOURce1:VOLTage:OFFSet {}".format(0))

	    self.instrument.write("FUNC:NOISe:BWIDth 50000000")

	    #self.instrument.write("SOURce1:FREQuency {}".format(10e6))
	    self.instrument.write("OUTPut1 ON")
            #self.instrument.write("APPL:SIN {},{},{}".format(freq, ampl, offset))
            print("Outputting noise now.")

    def close(self):
        self.instrument.write("OUTPut1 OFF")
        self.instrument.write("OUTPut2 OFF")
        self.instrument.close()

    def send_cmd(self, command):
        self.instrument.write("{}".format(command))

if __name__ == '__main__':
    exception = None
    fg = None
    try:
        fg = Agilent33600A()
        #fg.apply_pulse(1.0E3, 0.040, 0,5)
	time.sleep(2)
        #fg.apply_trigger_pulse(1.0E3, 2.5, 0,1000)
	#ampl=0.1
        #fg.apply_pulse(100,0.2, 0, 5e-9)
	
	#fg.apply_sin(100e6, 0.1)
	#time.sleep(10)
        #fg.sendcmd("PULS:WIDTH 5e-9")
        #fg.send_cmd("OUTPut2 OFF")
	#time.sleep(2)
        fg.send_cmd("OUTPut1 OFF")
        fg.send_cmd("OUTPut2 OFF")
        fg.close()
    except:
        exception = sys.exc_info()

    if exception:
        print("Failed to connect.")
        time.sleep(1)
        if fg:
            fg.close()
        raise SystemExit


