
#!/usr/bin/python
import sys
import numpy as np
import time
import target_driver
import matplotlib.pyplot as plt
import datetime
#Wisconsin specific modules:
import powerCycle
#import AgilentMSO9254
#import Keithley2200
import Keithley2000
import Keithley2200
import Agilent33600A
import piCom
import os
#import MSO9254
import scope_control
import csv

asic = 2

VpedScan_ena=0
trigEnable_ena=0
threshScan_ena=1
pulseScan_ena=0
noise_ena=0
gainScan_ena=0
wbiasScan_ena=0
wbiasTest_ena=0
PMTref4Scan_ena=0
PMTref4_optim=0
temperatureTest_ena=0
dynRangeTest_ena=0

homedir = os.environ['HOME']
timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
#baseDir = "/Users/tmeures/module3/T5TEATesting/"+dataset
#baseDir = "{}/target5and7data/testData2019/module3/T5TEATesting/{}".format(homedir, dataset)
baseDir = dataset + '/'
try:
        print "Trying to create directory."
        os.mkdir(baseDir)
        print "Created directory."
        os.chmod(baseDir, 0o777)
        print "directory", baseDir, "created."
except:
        print sys.exc_info()
        print "directory", baseDir, "already exists."







def testVped(module, asic, channel, multimeter, outputDir):
	"""1) Vped_0 --> 15: DAC value, Offset for Signal Chan 0
		Test procedure: Change value channel by channel. This should cause a change in the Amon output."""
	vped_name = 'Vped_'+str(channel)

	amonSelect = (channel/4) << 2
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)

	f = open(outputDir+"/VpedScan_asic"+str(asic)+"_channel"+str(channel)+".txt", 'w')
	for i in range(15):
		setting = 500+i*100
		module.WriteTriggerASICSetting(vped_name, asic, setting, False)
		time.sleep(0.4)
		multimeter.read()
		voltage = multimeter.voltage
		f.write( str(asic) +"\t"+str(channel)+"\t"+str(setting)+"\t"+str(voltage)+"\n" )
		print( str(asic)+"\t"+str(channel)+"\t"+str(setting)+"\t"+str(voltage) )

    	module.WriteTriggerASICSetting(vped_name,asic, 1200,False)
	f.close()


def Efficiency(module, trig_eff_duration):
    module.WriteSetting("TriggerEff_Duration", trig_eff_duration)
    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    ret, N = module.ReadSetting("TriggEffCounter")
    return N


def threshScan(module, asic,group, outputDir, trigger_duration, filename, pmtref4_start=1300, pmtref4_stop=2100, stepsize=10 ):

	countrate = np.zeros([2,int((pmtref4_stop-pmtref4_start)/stepsize)])

	trig_eff_duration = int(trigger_duration / 8. * 1e9)


    	module.WriteSetting("TriggerEff_Enable", 2**group)
    	f = open(filename,'w')
    	index = 0
	tempRate=0
	tempThresh=0
    	for pmtref4 in range(pmtref4_start,pmtref4_stop,stepsize):
			pmtref4_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(pmtref4_name,int(group/4),pmtref4, True)
			time.sleep(0.01)
			counts=Efficiency(module,trig_eff_duration)
			rate=counts*1.0/trigger_duration/1000.0
			if(abs(rate-0.5) < abs(tempRate-0.5) ):
				tempThresh = pmtref4
				tempRate = rate
			ret, temp =  module.GetTempI2CAux()
			ret,alert=module.ReadSetting("TempAlert_Aux")
			print ("group",group,"Thresh ",pmtref4," Counts ",counts, " Rate in kHz",rate, "Temperature:", temp, "Alert:", alert)
			countrate[0,index]=pmtref4
			countrate[1,index]=rate
			f.write(str(pmtref4)+"\t"+str(counts)+"\t"+str(rate)+"\t"+str(temp) +"\t"+str(alert)+"\n")
			index=index+1
			module.WriteTriggerASICSetting(pmtref4_name,int(group/4),0, True)
    	f.close()
	return tempThresh, tempRate


def testThreshScan(module, asic, channel, outputDir,ampl, ssh):



	amonSelect = (channel/4) << 2
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)

	#time.sleep(1)
	trigger_duration =0.2

	#time.sleep(1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(5)
	group = channel/4+asic*4
	print "The group is:", group


	#module.WriteSetting("TACK_EnableTrigger",2**group)
	filename=outputDir+'/threshScan_ampl_'+str(int(ampl*1000))+'_g_'+str(group)+'_ch_'+str(channel)+'.dat'
	threshScan(module, asic,group, outputDir, trigger_duration,filename)
	#threshScan(module, asic,group, outputDir, trigger_duration, filename, pmtref4_start=0, pmtref4_stop=3000, stepsize=50 )
	#trigger_enable_name = "TriggerEnable_Ch"+str(channel)
	#module.WriteTriggerASICSetting(trigger_enable_name, asic, 0, False)

	#threshScan(module, asic,group+8, outputDir, trigger_duration)

	piCom.setChannel(ssh,0)
	time.sleep(2)#This sleep time seems necessary to accomodate the piCom comman dabove
	#module.WriteTriggerASICSetting(trigger_enable_name, asic, 1, False)


def preparePulseScan(module, asic, channel, outputDir, ssh):
	fg = Agilent33600A.Agilent33600A()
	real_ampl = 0.02
	ampl = real_ampl * 2.0 / 0.6
	print("the set amplitude is:", ampl)
	fg.apply_pulse(1.0E3, ampl, 0,5)

	trigger_duration =0.2

	#time.sleep(1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(5)
	group = channel/4+asic*4
	print "The group is:", group


	#module.WriteSetting("TACK_EnableTrigger",2**group)
	filename=outputDir+'/threshScan_coarse_ampl_'+str(int(ampl*1000))+'_g_'+str(group)+'_ch_'+str(channel)+'.dat'
	tempThresh, tempRate = threshScan(module, asic,group, outputDir, trigger_duration, filename, pmtref4_start=1000, pmtref4_stop=1600, stepsize=10 )
	print("The coarse threshold result is:", tempThresh, "with rate", tempRate)

	trigger_duration =0.5

	filename=outputDir+'/threshScan_fine_ampl_'+str(int(ampl*1000))+'_g_'+str(group)+'_ch_'+str(channel)+'.dat'
	fineThresh, fineRate = threshScan(module, asic,group, outputDir, trigger_duration, filename, pmtref4_start=tempThresh-10, pmtref4_stop=tempThresh+10, stepsize=1 )
	print("The fine threshold result is:", fineThresh, "with rate", fineRate)
	
	fg.send_cmd("OUTPut1 OFF")
	fg.close


	return fineThresh



def testPulseScan(module, asic, channel, outputDir,thresh, ssh):



	amonSelect = (channel/4) << 2
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)

	#time.sleep(1)
	trigger_duration = 1.0

	#time.sleep(1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(5)
	group = channel/4+asic*4
	print "The group is:", group, "the ASIC:", asic


	module.WriteSetting("TACK_EnableTrigger",2**group)
	filename=outputDir+'/pulseScan'+'_g_'+str(group)+'_ch_'+str(channel)+'.dat'

	ampl_start=54
	ampl_stop=78
	stepsize = 0.6

	countrate = np.zeros([2, 40])

	trig_eff_duration = int(trigger_duration / 8. * 1e9)


	#module.WriteSetting("TriggerEff_Enable", 2**group)
	f = open(filename,'w')
	index = 0
	thresh_name='Thresh_'+str(int(group%4))
	thresh_value = thresh
	module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh_value, True)
	print("Wrote", thresh_value, "to setting:", thresh_name, "of ASIC", int(group/4) )
	fg = Agilent33600A.Agilent33600A()
	for i in range(40):
		ampl = ampl_start + i * stepsize
		fg.apply_pulse(1.0E3, ampl/1000.0, 0,5)
		time.sleep(0.2)
		counts=Efficiency(module,trig_eff_duration)
		rate=counts*1.0/trigger_duration/1000.0
		ret, temp =  module.GetTempI2CAux()
		print ("group",group, "Channel", channel,"Input amplitude setting ",ampl," Counts ",counts, " Rate in kHz",rate, "Temperature:", temp)
		countrate[0,index]=ampl
		countrate[1,index]=rate
		f.write(str(ampl)+"\t"+str(counts)+"\t"+str(rate)+"\t"+str(temp)+"\n")
	f.close()

	fg.send_cmd("OUTP OFF")
	fg.close

    #trigger_enable_name = "TriggerEnable_Ch"+str(channel)
	#module.WriteTriggerASICSetting(trigger_enable_name, asic, 0, False)

	#threshScan(module, asic,group+8, outputDir, trigger_duration)

	piCom.setChannel(ssh,0)
	time.sleep(2)#This sleep time seems necessary to accomodate the piCom comman dabove
	#module.WriteTriggerASICSetting(trigger_enable_name, asic, 1, False)


def testTriggerEnable(module, asic, channel, outputDir,ssh):


	#time.sleep(1)
	trigger_duration = 0.2

	#time.sleep(1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(2)
	group = channel/4+asic*4
	print "The group is:", group

	amonSelect = (channel/4) << 2
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)

	#Right now, this actually means just the gain is rewritten with the trigger disabled.
	triggerEnable = 0x15 << 2
	register = channel*2 +1
	print "Set Trigger enable for channel", channel, "with register value", triggerEnable, hex(triggerEnable)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,register,triggerEnable,True)

	filename=outputDir+'/trigEnaScan_0_'+str(group)+'_'+str(channel)+'.dat'
	threshScan(module, asic,group, outputDir, trigger_duration,filename)


	triggerEnable = (0x15 << 2) + 0x100
	register = channel*2 +1
	print "Set Trigger enable for channel", channel, "with register value", triggerEnable, hex(triggerEnable)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,register,triggerEnable,True)


	filename=outputDir+'/trigEnaScan_1_'+str(group)+'_'+str(channel)+'.dat'
	threshScan(module, asic,group, outputDir, trigger_duration,filename)



	piCom.setChannel(ssh,0)
	time.sleep(2)#This sleep time seems necessary to accomodate the piCom comman dabove
	#module.WriteTriggerASICSetting(trigger_enable_name, asic, 1, False)


def testTriggerGain(module, asic, channel, outputDir,ssh):


	#time.sleep(1)
	trigger_duration = 0.2

	#time.sleep(1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(3)
	group = channel/4+asic*4
	print "The group is:", group
	gainList = [0x0,0x1,0x5,0x15]
	for i in range(4):
		gain = gainList[i]  #  (i)/2*16 + (i%2)*5
		print "The gain is:", gain, hex(gain)
		trigGain_name = "TriggerGain_Ch"+str(channel)
		module.WriteTriggerASICSetting(trigGain_name,int(group/4),gain, True)
 	   	filename=outputDir+'/gain'+str(gain)+'_threshScan_'+str(group)+'_'+str(channel)+'.dat'
		threshScan(module, asic,group, outputDir, trigger_duration,filename)
	module.WriteTriggerASICSetting(trigGain_name,int(group/4),0x15, True)


	piCom.setChannel(ssh,0)
	time.sleep(2)#This sleep time seems necessary to accomodate the piCom comman dabove

def testWbias(moduel, asic, channel, outputDir, ssh):
	values = np.loadtxt(homedir+"/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")

	#time.sleep(1)
	#mso = MSO9254.MSO9254()
	#time.sleep(1)
	scope = scope_control.Scope()
	time.sleep(0.1)
	scope.configure()
	time.sleep(0.1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(1)
	scope.configure_pulse_width()
	scope.configure_delta_time()

	group = channel/4+asic*4
	print "The group is:", group

	thresh = 1750 #int(values[group%4,2])
	print "the used threshold is:", thresh

	filename = outputDir+'/wbiasTest_'+str(channel)+'.dat'
	datafile = open(filename, 'w')
	#datawriter = csv.writer(datafile, delimiter=',')
	#datawriter.writerow(['ASIC', 'Group', 'Wbias_Setting', 'Delay', 'Width', 'DelaySTD', 'WidthSTD'])
	paramList = ['ASIC', 'Group', 'Wbias_Setting', 'Delay', 'Width', 'DelaySTD', 'WidthSTD']
	for p in range(len(paramList)):
		datafile.write(paramList[p] + "    ")
	datafile.write("\n")


	thresh_name='Thresh_'+str(int(group%4))
	module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
	wbias_data = []
	wbias_setting = 1450
	wbias_name = 'Wbias_'+str(int(group%4))
	module.WriteTriggerASICSetting(wbias_name, int(group/4), wbias_setting, True)
	print("Wbias is: {}".format(wbias_setting))
	for i in range(100):
		width = scope.measure_pulse_width()
		delta = scope.measure_delta_time()
		if width[0] < 1.0 and delta[0] < 0.0 and delta[0] > -1.0:
			wbias_data.append([delta, width])
			print([delta, width])
	wbias_data = np.asarray(wbias_data)
	means = np.mean(wbias_data, axis=0)
	sigmas = np.std(wbias_data, axis=0)
	datafile.write("%f   %f   %f   %.2e   %.2e   %.2e   %.2e\n" % (asic, group, wbias_setting, means[0], means[1], sigmas[0], sigmas[1] ) )

	module.WriteTriggerASICSetting(wbias_name,int(group/4),0x43c, True)
	piCom.setChannel(ssh,0)
	time.sleep(1)#This sleep time seems necessary to accomodate the piCom comman dabove
	#mso.close()
	scope.close()
	datafile.close()

def testWbiasScan(module, asic, channel, outputDir, ssh):

	values = np.loadtxt(homedir+"/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")

	#time.sleep(1)
	#mso = MSO9254.MSO9254()
	#time.sleep(1)
	scope = scope_control.Scope()
	time.sleep(0.1)
	scope.configure()
	time.sleep(0.1)
	piCom.setChannel(ssh,channel+1)
	time.sleep(1)
	scope.configure_pulse_width()
	scope.configure_delta_time()

	group = channel/4+asic*4
	print "The group is:", group

	thresh = 1750 #int(values[group%4,2])
	print "the used threshold is:", thresh

	filename = outputDir+'/wbiasScan_'+str(group)+'.dat'
	datafile = open(filename, 'w')
	#datawriter = csv.writer(datafile, delimiter=',')
	#datawriter.writerow(['ASIC', 'Group', 'Wbias_Setting', 'Delay', 'Width', 'DelaySTD', 'WidthSTD'])
	paramList = ['ASIC', 'Group', 'Wbias_Setting', 'Delay', 'Width', 'DelaySTD', 'WidthSTD']
	for p in range(len(paramList)):
		datafile.write(paramList[p] + "    ")
	datafile.write("\n")


	thresh_name='Thresh_'+str(int(group%4))
	module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)

	for i in range(20):
		wbias_data = []
		wbias_setting = 950 + i * 25
		wbias_name='Wbias_'+str(int(group%4))
		module.WriteTriggerASICSetting(wbias_name,int(group/4),wbias_setting, True)
		print("Wbias is: {}".format(wbias_setting))
		#raw_input("Hit enter if acquisition is complete")
		for i in range(100):
			width = scope.measure_pulse_width()
			delta = scope.measure_delta_time()
			#delta = 0.0
			#time.sleep(0.5)

			#time.sleep(0.5)
			wbias_data.append([delta, width])
			print([delta, width])
		wbias_data = np.asarray(wbias_data)
		means = np.mean(wbias_data, axis=0)
		sigmas = np.std(wbias_data, axis=0)
		print(means)
		print(sigmas)
		#datawriter.writerow([asic, group, wbias_setting, means[0], means[1], sigmas[0], sigmas[1]])
		datafile.write("%f   %f   %f   %.2e   %.2e   %.2e   %.2e\n" % (asic, group, wbias_setting, means[0], means[1], sigmas[0], sigmas[1] ) )

			#print("delta: {}, width: {}".format(delta, width))

        #dt = mso.measureDelay()
		#print "The delay is:", dt
		#dt = mso.measureWidth()
		#print "The width is:", dt
		#Read Scope stuff here!!!!!
		#time.sleep(5)
	#Back to default
	module.WriteTriggerASICSetting(wbias_name,int(group/4),0x43c, True)
	piCom.setChannel(ssh,0)
	time.sleep(1)#This sleep time seems necessary to accomodate the piCom comman dabove
	#mso.close()
	scope.close()
	datafile.close()

def testPMTref4(module, asic, channel, multimeter, outputDir):
	"""1) Vped_0 --> 15: DAC value, Offset for Signal Chan 0
		Test procedure: Change value channel by channel. This should cause a change in the Amon output."""
	pmtref_name = 'PMTref4_'+str(channel/4)

	amonSelect = (channel/4) << 2
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	#Write Amon value:
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)

	f = open(outputDir+"/PMTref4Scan_asic"+str(asic)+"_channel"+str(channel)+".txt", 'w')

	for i in range(100):
		setting = 1500+i*10
		module.WriteTriggerASICSetting(pmtref_name, asic, setting, False)
		time.sleep(0.4)
		multimeter.read()
		voltage = multimeter.voltage
		f.write( str(asic) +"\t"+str(channel)+"\t"+str(setting)+"\t"+str(voltage)+"\n" )
		print( str(asic)+"\t"+str(channel)+"\t"+str(setting)+"\t"+str(voltage) )


    	#module.WriteTriggerASICSetting(pmtref_name,asic, 2130,False)

def testPMTref4_optim(module, asic, channel, multimeter, outputDir):
	pmtref_name = 'PMTref4_'+str(channel/4)

	amonSelect = (channel/4) << 2
	#Write Amon value:
	print "Set Amon to group", channel/4, "with register value", amonSelect, hex(amonSelect)
	module.WriteTARGETRegister(True,True,True,True,False,True,0x36,amonSelect,True)


	refVoltage = 1.75
	setting = 1902
	multimeter.read()
	voltage = multimeter.voltage
	print("The voltage before changing:", voltage)
	print("The settings are:", pmtref_name, asic, setting)
	module.WriteTriggerASICSetting(pmtref_name, asic, setting, False)
	time.sleep(1)
	multimeter.read()
	voltage = multimeter.voltage
	measured = voltage
	print("The first voltage:", voltage)
	changeSetting = 10
	changeVoltage = 0
	stepCount=0
	while(abs(refVoltage-voltage)>0.003 and stepCount<40):
		if(changeVoltage==0):
			if(voltage > refVoltage):
				changeSetting = -10
			else:
				changeSetting = 10
		else:
			changeSetting = int(  ( (refVoltage-voltage)*1.0/changeVoltage )*abs(changeSetting) )
			print refVoltage, voltage, changeVoltage, ( (refVoltage-voltage)*1.0/changeVoltage ), changeSetting

		if(changeSetting>500):
			changeSetting=500
		if(changeSetting==0):
			if(voltage>refVoltage):
				changeSetting=-1
			else:
				changeSetting=1

		setting = setting+changeSetting
		if(setting> 4095 and setting<0):
			break

		temp = voltage
		print(setting)
		module.WriteTriggerASICSetting(pmtref_name, asic, setting, False)
		time.sleep(3)
		voltage = 0
		for rr in range(5):
			multimeter.read()
			voltage+=multimeter.voltage/5.0
			#print voltage, multimeter.voltage

		changeVoltage=abs( voltage - temp)
		stepCount+=1

        	print("Change pmt_ref4 by: {} to {} \n Reading voltage: {}".format(changeSetting, setting, voltage))

	#f = open(homedir+"/target5and7data/testData2019/module3/T5TEATesting/PMTref4_levels_old.txt",'a')
	f = open(homedir+"/PMTref4_levels_high.txt",'a')
	f.write( str(asic) +"\t"+str(channel)+"\t"+str(setting)+"\t"+str(voltage)+"\n" )
	f.close()



def checkControl(module, asic):



	outputDir = baseDir
	if(PMTref4Scan_ena or PMTref4_optim):
		multimeter = Keithley2000.Keithley2000()
		multimeter.configure(readMode='voltage')

		for channel in range(0,16,4):
			if PMTref4Scan_ena:
				testPMTref4(module, asic, channel, multimeter, outputDir)
			if PMTref4_optim == 1:
				testPMTref4_optim(module, asic, channel, multimeter, outputDir)
			else:
				print("That was useless")
		multimeter.close()

	if(VpedScan_ena):
		multimeter = Keithley2000.Keithley2000()
		multimeter.configure(readMode='voltage')

		for channel in range(16):
			testVped(module, asic, channel, multimeter, outputDir)

		multimeter.close()



	if(threshScan_ena):
		fg = Agilent33600A.Agilent33600A()
		if(noise_ena):
			ampl = 0.08
			fg.apply_noise(ampl,0)
		else:
			real_ampl = 0.012
			#real_ampl = 0.02
			ampl = real_ampl * 2.0 / 0.6
			fg.apply_pulse(1.0E3, ampl, 0,10)

		ssh = piCom.executeConnection()
		for channel in range(12,16):
			testThreshScan(module, asic, channel, outputDir, ampl,ssh)

		fg.send_cmd("OUTPut1 OFF")
		
		if(noise_ena):
			ampl = 0.01
			fg.apply_noise(0.01,0)
		else:
			real_ampl = 0.006
			ampl = real_ampl * 2.0 / 0.6
			fg.apply_pulse(1.0E3, ampl, 0,10)

		ssh = piCom.executeConnection()
		for channel in range(12,16):
			testThreshScan(module, asic, channel, outputDir, ampl,ssh)

		fg.send_cmd("OUTPut1 OFF")
		
		fg.close

	if(pulseScan_ena):
		ssh = piCom.executeConnection()
		#thresh = 1387
		for channel in range(8,16):
			thresh = preparePulseScan(module, asic, channel, outputDir, ssh)
			
			testPulseScan(module, asic, channel, outputDir, thresh, ssh)

	if(gainScan_ena):
		fg = Agilent33600A.Agilent33600A()
		fg.apply_pulse(1.0E3, 0.050, 0,5)
		fg.send_cmd("PULS:WIDTH 5e-9")

		ssh = piCom.executeConnection()
		for channel in range(16):
			testTriggerGain(module, asic, channel, outputDir,ssh)

		fg.send_cmd("OUTP OFF")
		fg.close

	if(trigEnable_ena):
		fg = Agilent33600A.Agilent33600A()
		fg.apply_pulse(1.0E3, 0.050, 0,5)
		fg.send_cmd("PULS:WIDTH 5e-9")

		ssh = piCom.executeConnection()
		for channel in range(16):
			testTriggerEnable(module, asic, channel, outputDir,ssh)

		fg.send_cmd("OUTP OFF")
		fg.close

	if(wbiasScan_ena):
		fg = Agilent33600A.Agilent33600A()
		fg.apply_pulse(1.0E3, 0.2, 0,5)
		fg.send_cmd("PULS:WIDTH 5e-9")

		ssh = piCom.executeConnection()
		for channel in range(0, 16, 4):

			probeLocation = raw_input("Probe connected to channel{}? (1=YES, 0=NO)".format(channel))
			testWbiasScan(module, asic, channel, outputDir,ssh)

		fg.send_cmd("OUTP OFF")
		fg.close
	if(wbiasTest_ena):
		fg = Agilent33600A.Agilent33600A()
		fg.apply_pulse(1.0E3, 0.2, 0, 5)
		fg.send_cmd("PULS:WIDTH 5e-9")

		ssh = piCom.executeConnection()
		for channel in range(16):
			probeLocation = raw_input("Probe connected to channel{}?".format(channel))
			testWbias(module, asic, channel, outputDir, ssh)

		fg.send_cmd("OUTP OFF")
		fg.close

	if(temperatureTest_ena):



		ret, temp =  module.GetTempI2CAux()
		print ("Temperature Aux: ",temp)
		ret,alert=module.ReadSetting("TempAlert_Aux")
		print("Alert before",alert)
		#module.WriteSetting("I2CRW_Aux", 0)
		#module.WriteSetting("I2CRegAddr_Aux", 3)
		time.sleep(1)
		module.WriteRegister(0x29,0x3000000)
		temp=48.0
		dac=int(temp/0.0625)<<4
		correct_dac= ((dac & 0xFF ) << 8) + (dac >> 8)
		print("Set Aux upper temp limit to",temp,"C, DAC =",correct_dac)
		module.WriteSetting("I2CWriteData_Aux", correct_dac)
		#module.WriteSetting("I2CStart_Aux", 1)
		correct_dac_start = correct_dac + 0x80000000
		time.sleep(1)
		module.WriteRegister(0x2f,correct_dac_start)
		time.sleep(.5)
		ret, temp =  module.GetTempI2CAux()
		print ("Temperature Aux: ",temp)
		ret,alert=module.ReadSetting("TempAlert_Aux")
		print("Alert Aux after",alert)

		module.WriteRegister(0x29,0x2000000)
		temp=40.0
		dac=int(temp/0.0625)<<4
		correct_dac= ((dac & 0xFF ) << 8) + (dac >> 8)
		print("Set Aux lower temp limit to",temp,"C, DAC =",correct_dac)
		module.WriteSetting("I2CWriteData_Aux", correct_dac)
		#module.WriteSetting("I2CStart_Aux", 1)
		correct_dac_start = correct_dac + 0x80000000
		module.WriteRegister(0x2f,correct_dac_start)
		time.sleep(.5)
		ret, temp =  module.GetTempI2CAux()
		print ("Temperature Aux: ",temp)
		ret,alert=module.ReadSetting("TempAlert_Aux")
		print("Alert Aux after",alert)
		#The default is good.
		#module.WriteSetting("I2CRW_Aux", 0)  #--> We want to write to the bus
		#module.WriteRegister(0x29,0x3000000)
		#module.WriteRegister(0x2a,0x9000)
		#module.WriteSetting("I2CRegAddr_Aux", 0x3) #--> Write to the high temperature limit
		#The temperature format can be found on page 12 #
		#try example: 35 degree = 560*0.0625 --> Setting should be: 0 0010 0011 0000 = 0x230
		#module.WriteRegister(0x2f,0x2300)
		#module.WriteSetting("I2CWriteData_Aux", 0x230) #<- this is 8 bits only.We would need two bytes: 0x2, 0x30
		#print("Writing temperature now!")
		#time.sleep(1)
		#module.WriteRegister(0x2f,0x80002300)
		#module.WriteSetting("I2CStart_Aux", 1)   #Start the actual operation.
		#time.sleep(0.1)
		#module.WriteRegister(0x2f,0x0)



		#fg = Agilent33600A.Agilent33600A()
		#if(noise_ena):
		#	ampl = 0.08
		#	fg.apply_noise(ampl,0)
		#else:
		#	real_ampl = 0.012
		#	ampl = real_ampl * 2.0 / 0.6
		#	fg.apply_pulse(1.0E3, ampl, 0,5)

		#ssh = piCom.executeConnection()
		for rep in range(10):
			outputDir_rep = outputDir + "/"+str(rep) + "/"
			os.mkdir(outputDir_rep)
			os.chmod(outputDir_rep, 0o777)
			channel=0
			group = channel/4+asic*4
			ampl = 0.040
			filename=outputDir_rep+'/threshScan_ampl_'+str(int(ampl*1000))+'_g_'+str(group)+'_ch_'+str(channel)+'.dat'
			trigger_duration = 0.2
			#for channel in range(1):
				#testThreshScan(module, asic, channel, outputDir_rep, ampl,ssh)
			threshScan(module, asic, group, outputDir, trigger_duration, filename)



		#fg.send_cmd("OUTPut1 OFF")

	if(dynRangeTest_ena):
		fg = Agilent33600A.Agilent33600A()
		for a in range(1,15):
			real_ampl = a*0.01
			#real_ampl = 0.02
			ampl = real_ampl * 2.0 / 0.6
			fg.apply_pulse(1.0E3, ampl, 0,10)

			ssh = piCom.executeConnection()
			for channel in range(0,16,1):
				testThreshScan(module, asic, channel, outputDir, ampl,ssh)

			fg.send_cmd("OUTPut1 OFF")



	"""This function works through all settable registers to understand if they react in the expected way to the setting."""
	"""Potential settings are:
	1) Vped_0 --> 15: DAC value, Offset for Signal Chan 0
		Test procedure: Change value channel by channel. This should cause a change in the Amon output.
	2) TriggerGain_Ch0 --> 15: Trigger gain: Select resistor value for trigger gain in channel 0: There are 4 options: 0x0 -> 5kOhm,
		0x01 -> 5kOhm/2, 0x05 0x01 -> 5kOhm/3, 0x15-> 5kOhm/4
	3) TriggerEnable_Ch0 --> 15:  Enable trigger in channel 0, if 0 the pedestal is sent to the summing amplifier, if
		1 pedestal + AC-input signal is sent to the summing amplifier
	4) Wbias_0-3: 0x43c DAC value, controls the width of the digital trigger output pulses for the 0th group of channels (0-3),
		default value corresponds to XX ns, user should set appropriate value for trigger operations
	5) Thresh_0-3: 0x0 DAC value, controls reference voltage for digitial trigger output (i.e. sets the trigger threshold) in the
		0th group of channels (0-3), 0x000 corresponds to the highest possible threshold, user should set appropriate value
		for trigger operations.
	6) PMTref4_0-3: 0xFFF DAC value, controls reference voltage for summing amplifier in the 0th group of channels (0-3), default
		of 0xFFF corresponds to the highest possible threshold, user should set appropriate value for trigger operations
	7) TTbias_0-3: 0x44C DAC value, controls supply bias for the two voltages PMTref4 and Thresh for the 0th group of channels (0-3)
	8) TTbias_C: 0x3E8 DAC value, controls supply bias for VpedBias, TRGBias,TRGSumBias, TRGBias
	9) VpedBias: 0x708 DAC value, controls supply bias for internal VPED (Offset) generation
	10) TRGsumbias: 0x640 DAC value, controls supply bias for trigger summing amplifiers --- CHANGED FROM 0x384 to 0x640 (RW on
		advice from AZ d2019-04-16)
	11) TRGGbias: 0x640 DAC value, controls supply bias for the first pre-amplifier of the trigger input
	12) TRGbias: 0x3E8 DAC value, controls supply bias for the trigger comparators
	13) CMPThresh: 0xFA0 DAC value, voltage to compare with Analog monitoring output
	14) SGN: 0x0 selects the sign of the trigger edge, 0 - rising edge, 1 - falling edge
	15) AmonSelect: 0x0 Select which of the trigger groups summing amplifier output i    s sent to the ASIC Analog
		monitoring output: 0 - group 0, 1 - group 1, 2 -group 2, 3 - group 3
	16) TTbias_A: 0x0 DAC value, controls supply bias for Analog monitoring output
	"""


bps = Keithley2200.Keithley2200()
bps.powerModuleOn()

time.sleep(10)
#Define if new initialization is needed:
initialize = True

#duration of trigger count period in s


#path to def files
module_def = homedir+"/svn_folder/CCC/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000004.def"
asic_def = homedir+"/TargetDriverTrunk/config/TC_ASIC.def"
#trigger_asic_def = "/Users/tmeures/svn_folder/CCC/TargetDriver/branches/issue37423/config/T5TEA_ASIC.def"
trigger_asic_def = homedir+"/TargetDriverTrunk/config/T5TEA_ASIC.def"
#trigger_asic_def = "/Users/tmeures/TargetDriver_issue37423/config/T5TEA_ASIC.def"
#computer ip

module_def = "{}/pSCT_module_control/svn_folder/CCC/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000002.def".format(homedir)
asic_def = "{}/pSCT_module_control/svn_folder/CCC/TargetDriver/trunk/config/TC_ASIC.def".format(homedir)
trigger_asic_def = "{}/pSCT_module_control/svn_folder/CCC/TargetDriver/trunk/config/T5TEA_ASIC.def".format(homedir)

my_ip = "192.168.12.1"
#eval module ip
module_ip = "192.168.12.173"


#Define the targetModule object
module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)


if initialize:
    #In case of a reinitialization an connection needs to be established to the targetModule. It needs to be reset and all default parameters need to be written.
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)
    #module.WriteSetting("SetDataPort", 8107)
    #module.WriteSetting("SetSlowControlPort", 8201)


for aa in range(4):
  module.WriteTriggerASICSetting("VpedBias", aa, 1800, True)
  for channel in range(16):
    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
    module.WriteTriggerASICSetting("Vped_{}".format(channel), aa, 1200 ,True)#int(content[asic*16+channel]), True)
time.sleep(1)

### Setting optimized SSToutFB & VtrimT ###
#data = ascii.read(VTRIM_FILE)
#print(data)
for aa in range(4):
  #print("Setting SSToutFB_Delay of Asic " + str(asics) + " to " + str(int(data[asics][2])))
  module.WriteASICSetting("SSToutFB_Delay", aa, 58,True,False)#int(data[asics][2]), True, False) # standard value: 58
  #print("Setting VtrimT of Asic " + str(asics) + " to " + str(int(data[asics+4][2])))
  module.WriteASICSetting("VtrimT", aa, 1240,True,False)#int(data[asics+4][2]), True, False) # standard value: 1240
time.sleep(1)

#module.SetVerbose()
module.WriteSetting("SR_DisableTrigger",0x1)

ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

#disable data trigger
module.WriteSetting("TACK_EnableTrigger",0)

module.WriteTriggerASICSetting("Wbias_0", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_1", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_2", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_3", 0, 985, False)



#filename = homedir + "/target5and7data/testData2019/module3/T5TEATesting/PMTref4_levels.txt"
filename = homedir + "/PMTref4_levels.txt"
#filename = homedir + "/PMTref4_levels_high.txt"

dat = np.loadtxt(filename)
for l in range(4):
	print(dat[l*4,0], dat[l*4,2])
	module.WriteTriggerASICSetting("PMTref4_0", int(dat[l*4,0]), int(dat[l*4,2]), True)
	module.WriteTriggerASICSetting("PMTref4_1", int(dat[l*4,0]), int(dat[l*4+1,2]), True)
	module.WriteTriggerASICSetting("PMTref4_2", int(dat[l*4,0]), int(dat[l*4+2,2]), True)
	module.WriteTriggerASICSetting("PMTref4_3", int(dat[l*4,0]), int(dat[l*4+3,2]), True)









module.WriteTriggerASICSetting("Thresh_0", 0,0, False)
module.WriteTriggerASICSetting("Thresh_1", 0,0, False)
module.WriteTriggerASICSetting("Thresh_2", 0,0, False)
module.WriteTriggerASICSetting("Thresh_3", 0,0, False)

module.WriteTriggerASICSetting("TTbias_A", 0,0x543, False)

#module.WriteSetting("DurationofDeadtime",25000)

print("Setup completed!")
"""
time.sleep(10)
time.sleep(1)
voltage = 0
multimeter = Keithley2000.Keithley2000()
multimeter.configure(readMode='voltage')
for rr in range(5):
	multimeter.read()
	voltage+=multimeter.voltage/5.0
print("The voltage is:", voltage)

time.sleep(3)
"""
checkControl(module, asic)


module.CloseSockets()
bps.powerModuleOff()


