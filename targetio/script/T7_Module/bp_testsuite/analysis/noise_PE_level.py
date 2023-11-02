################################################################
# To use this script you must input the following paramters:   #
#   Rate of interest                                           #
#   List of files you want to analyse                          #
#   Saved file name                                            #
#   Resulting plot is saved onto desktop                       #
################################################################

# import libraries you'll need
import numpy as np
import matplotlib.pyplot as plt
import os.path

# frequently used file paths
homedir = os.environ['HOME']
desktop = homedir+'/Desktop/'

# function for interpolation
def interpolateX(dat1, dat2, yPos):
    m = (dat1[1]-dat2[1])/(dat1[0]-dat2[0])
    b = dat1[1]-(m*dat1[0])
    xPos = (yPos-b)/m
    return xPos

######################################################
# INPUT RATE AND FILES HERE 
rate = 1000
fileList = [0]
labelList= []
save_file_name = 'my_file'

# -----------------------------------------------------------------
data_array = np.zeros((len(fileList),16,1))
trig = np.arange(0,16,1)
max_thresh_val = np.zeros((16,17))
pe_array = np.zeros((len(fileList),16))

counter = 0
for run in fileList:
    if run==0:
        dirname =  '/Users/newowner/Documents/CTA/Data/2018/022118/108_old_VR'
        label = '108 old VR'
    labelList.append(label)

###################################################################################################


    data1= []            
    for asic in range(4):
        for group in range(4):
            filename=dirname+"/a{}g{}".format(asic,group)+".txt"
            if(os.path.isfile(filename) ):
                #print("Reading values: "), asic, group, filename
                data1.append(np.loadtxt(filename) )   
                
    for j in range(16):
        for i in range(1,len(data1[run])):
            if(data1[j][i,1]>= rate):
                dat1 = [data1[j][i,0], data1[j][i,1]] 
                dat2 = [data1[j][i-1,0], data1[j][i-1,1]]
                thresh = interpolateX(dat1, dat2, rate)
                data_array[counter,j] = thresh
                break
            if(i==len(data1[0])-1):
                data_array[run,j] = data1[j][i,0]
            #print(thresh) #thresh for asic(0,1,2,3) and group 1
    counter+=1 
            
# data for creating map
fileList1=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
DACList = [1081,1086,1091,1096,1101,1106,1111,1116,1121,1126,1131,1136,1141,1146,1151,1156,1161,1166,1171,1176,1181,1186,1191,1196,1201]
pedList = []
data=[]

for file in fileList1:
    if(file==0): 
        dirname = '/Users/newowner/Documents/CTA/Data/2017/080817/1240'
    if(file==1):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1323'
    if(file==2):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1405'
    if(file==3):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1447'
    if(file==4):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1529'
    if(file==5):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1611'
    if(file==6):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1653'
    if(file==7):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1735'
    if(file==8):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1817'
    if(file==9):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1859'
    if(file==10):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/1941'
    if(file==11):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2023'
    if(file==12):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2105'
    if(file==13):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2147'
    if(file==14):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2229'
    if(file==15):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2311'
    if(file==16):
        dirname= '/Users/newowner/Documents/CTA/Data/2017/080817/2353'

    pedList.append((0.609*(DACList[file]) + 26.25))
    roundedPed = [round(item, 4) for item in pedList]
    
    for asic in range(4):
        for group in range(4):
            filename=dirname+"/a{}g{}".format(asic,group)+".txt"
            if(os.path.isfile(filename) ):
                #print("Reading values: "), asic, group, filename
                data.append(np.loadtxt(filename))
                
pedArray = np.asarray(pedList)


# make map
for asic in range(4):
    for group in range(4):
        for run in range(17):
            maxRate = []
            maxThresh = []
            for j in range((len(data[(asic*4+group)+run*16]))):
                if (data[(asic*4+group)+run*16][j,1]>1E7):
                    maxRate.append(data[(asic*4+group)+run*16][j,1])
                    maxThresh.append(data[(asic*4+group)+run*16][j,0])
    
            if len(maxRate)>1.0:
                meanThresh = np.mean(maxThresh)
                max_thresh_val[asic*4+group,run]=(meanThresh)
            
            if len(maxRate)==1.0:
                x = data[(asic*4+group)+run*16][:,0] 
                y = data[(asic*4+group)+run*16][:,1]
                max_y = np.amax(y)
                max_x = x[y.argmax()]
                max_thresh_val[asic*4+group,run]=(max_x)          

# convert crossing from thresh to PE
for run in range(len(fileList)):
    for gr in range(16):
        for ped in range(17):
            if max_thresh_val[gr,ped]<= data_array[run,gr]:
                dat1 = [pedList[ped], max_thresh_val[gr,ped]]
                dat2 = [pedList[ped-1], max_thresh_val[gr,ped-1]]
                volt = interpolateX(dat1, dat2, data_array[run,gr])
                break
        x1 = 4*(volt-699.804)
        PE = x1/4.0
        pe = round(PE,2)
        #print(x1, pe)
        pe_array[run,gr] = pe

# plot final result        
figure = plt.figure(figsize=(10,8))

for run in range(len(fileList)):
    plt.plot(trig, pe_array[run], marker='o', label=labelList[run])
plt.xlabel('Trigger Group', fontsize=25)
plt.ylabel('Single Channel Threshold at {}Hz Rate'.format(rate), fontsize=25)
plt.axvline(x=3, linestyle='--')
plt.axvline(x=7, linestyle='--')
plt.axvline(x=11, linestyle='--')
plt.tick_params(axis='x', labelsize=20)
plt.tick_params(axis='y', labelsize=20)
#plt.ylim(0,25)
plt.xlim(0,15)

lgd= plt.legend(bbox_to_anchor=(1.01, .9), fontsize=15, borderaxespad=0.)
figure.savefig('/Users/newowner/Desktop/{}.png'.format(save_file_name), bbox_extra_artists=(lgd,), bbox_inches='tight')