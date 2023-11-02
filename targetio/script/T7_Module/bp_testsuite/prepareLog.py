import os
import fnmatch
import sys
import shutil
import datetime
import time
import run_control
import logging
#import smtplib
#from email.mime.text import MIMEText
#Some input from the user:



#class StreamToLogger(object):
#   """
#   Fake file-like stream object that redirects writes to a logger instance.
#   """
#   def __init__(self, logger, log_level=logging.INFO):
#      self.logger = logger
#      self.log_level = log_level
#      self.linebuf = ''
# 
#   def write(self, buf):
#      for line in buf.rstrip().splitlines():
#         self.logger.log(self.log_level, line.rstrip())
 

def prepareLog(moduleID=None,FPM=None, name=None, purpose=None, logLevel=None, sendToFile=-1, outputDir="output"):
	#Some IO forth and back with the user.
	while (name==None):
		name =  raw_input("Please enter your name: ")
	
	#moduleID = None
	while not moduleID:
	    try:
	        moduleID = int(raw_input("Please enter the module id (i.ex. 111): "))
	    except ValueError:
	        print 'Invalid Number. The module id must be an integer.'
	

	if FPM != None:
		FPM = "{}.{}".format(FPM[0],FPM[1])
	else:
		FPM = raw_input("Please enter the FPM number.(i.ex. 4.1): ")

	while (purpose==None):
		purpose = raw_input("Input purpose of this test run: ")
	while logLevel==None:
		logLevel = int(raw_input("Chose logelevel: integer between 0 and 3 (ERROR=0, WARNING=1, INFO=2, DEBUG=3): ") )

	while sendToFile==-1:
 	       sendToFile = int(raw_input("Should the log be sent to a file (1=YES, 0=NO): "))


	
	timestamp = time.time()
	dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
	date = datetime.datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y')
	
	hostname = run_control.getHostName()
	outdirname = run_control.getDataDirname(hostname)
	
	testDir = outdirname + 'test_suite_output/FEE'+str(moduleID)+'FPM'+FPM
	try:
		os.mkdir(testDir)
		os.chmod(testDir, 0o777)
	except:
		print "directory", testDir, "already exists."
	
	outputDir = outputDir+"/testRun_{}".format(dataset)	
	try:
		os.mkdir(outputDir)
		os.chmod(outputDir, 0o777)
	except:
		print "directory", outputDir, "already exists."

	testLogFile = testDir+"/testRun_{}/testRun_{}".format(dataset,dataset)+".log"
	assocRun = outputDir+"/associatedRuns_{}".format(dataset)+".log"
	assocFile = outputDir+"/associatedFiles_{}".format(dataset)+".log"
	
	dstDir = testDir +"/oldTests"
	logFormat = "%(module)s :: %(funcName)s : %(msecs)d : %(message)s"

	newDir = ''
	oldDataset = 'hold'

	for file in os.listdir(testDir):
		if ( fnmatch.fnmatch(file, 'testRun*') ):
			inName = file.split(".")
			newDir = inName[0]
			oldDataset = "{}_{}".format(newDir.split("_")[-2], newDir.split("_")[-1])

			if ( fnmatch.fnmatch(file, '*{}*'.format(oldDataset)) ):
				print( "Found older testLog. Move it to subdirectory.")
				print( file )
				src = testDir +"/"+file
				srcDir = testDir +"/"+newDir
				finalDir = dstDir+"/"+newDir
				dst = finalDir +"/"+file

				try:
					os.mkdir(dstDir)
					os.chmod(dstDir,0o777)
				except:
					print "Directory", dstDir, "could not be created. It might already exist."

				try:
					shutil.move(srcDir, finalDir)
				except:
					print "Couldn't move", srcDir, "."

					try:
						os.mkdir(finalDir)
						os.chmod(finalDir,0o777)
					except:
						print "Directory", finalDir, "could not be created. It might already exist."

#				try:
#					shutil.move(src, dst)
#				except:
#					print "Couldn't move", src, ". Permission denied."


	outLevel = logging.ERROR

	if(logLevel==0):
		outLevel=logging.ERROR
		print "Log-level is:", logLevel
	if(logLevel==1):
		outLevel=logging.WARNING
		print "Log-level is:", logLevel
	if(logLevel==2):
		outLevel=logging.INFO
		print "Log-level is:", logLevel
	if(logLevel==3):
		outLevel=logging.DEBUG
		print "Log-level is:", logLevel
	
	if(sendToFile==1):
		logging.basicConfig(filename=testLogFile, format=logFormat, level=outLevel)
		print "Logging to file."
	else:
		logging.basicConfig(format=logFormat, level=outLevel)
		print "NOT Logging to file."

	logging.info("Test date: %s\n" % date)
	logging.info("Tester name: %s\n" % name)
	logging.info("Testing module: FEE%d\n" % moduleID)
	logging.info("In combination with focal plane: FPM%s\n" % FPM)
	logging.info("Purpose of the test: %s \n" % purpose)
	logging.info("===================================================================\n")
	logging.info("========================Starting test==============================\n")
	logging.info("===================================================================\n")


	testDirFinal = testDir
	fitsDir = outdirname
	testDir = outputDir
	return dataset, testDir, assocRun, assocFile, moduleID, FPM, purpose, name, testLogFile, testDirFinal, fitsDir 
	




'''
	stdout_logger = logging.getLogger('STDOUT')
	sl = StreamToLogger(stdout_logger, logging.INFO)
	sys.stdout = sl
 
	stderr_logger = logging.getLogger('STDERR')
	sl = StreamToLogger(stderr_logger, logging.ERROR)
	sys.stderr = sl
'''






'''
def endLog(dataset, emailAddress):
	
# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
##	fp = open(textfile, 'rb')
	# Create a text/plain message



	sender = '@.com'
	receivers = ['to@todomain.com']

message = """From: From Person <from@fromdomain.com>
To: To Person <to@todomain.com>
Subject: SMTP e-mail test

This is a test e-mail message.
"""

##try:
   smtpObj = smtplib.SMTP('localhost')
   smtpObj.sendmail(sender, receivers, message)         
   print "Successfully sent email"
##except SMTPException:
##   print "Error: unable to send email"
'''




