import sys, os
import shutil
import time

homedir = os.environ['HOME']
googleCSV = '/Users/colinadams/Google Drive/documentation_testsuite/report.csv'
desktopCSV = '{}/Desktop/report.csv'.format(homedir)

if os.path.isfile(googleCSV):
	#copy out
	shutil.copyfile(googleCSV,desktopCSV)
	#delete original
	os.remove(googleCSV)
	time.sleep(10)
	#move copy back in
	shutil.move(desktopCSV,googleCSV)

