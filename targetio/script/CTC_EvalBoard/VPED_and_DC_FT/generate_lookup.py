import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime

#if len(sys.argv) < 2 :
#    print("Not enough arguments!")
#    sys.exit()

#print("The arguments are: " , str(sys.argv))

#module_id = sys.argv[1]
serial_id = "SN0002"

data=np.zeros([16,512,3])
for i in range (16):
    try:
        data[i]=(np.loadtxt("data/VPED_TF_{}.txt".format(i)))
    except:
        print("File data/VPED_TF_{}.txt not found!".format(i))
vpeds=data[0,:,0].astype(int)

counts=0

voltages=np.arange(1,2501)
b=[]

for k in range(16):

  values=data[k,:,1]
  b.append(np.interp(voltages,values,vpeds,left=-1,right=-1))

b=np.array(b)
b=np.rint(b).astype(int)

for m in range(16):
    for j in range(100,2400):
        if b[m,j]==-1:
            continue
        previndex=j-1
        while(previndex>0):
            prev_val=b[m,previndex]
            if prev_val==-1:
                previndex-=1
            else:
                break
            if b[m,j]==prev_val or (b[m,j]==prev_val+1 and b[m,j-1]==-1):
                counts+=1
                b[m,j]=-1


np.savetxt("data/VPED_lookup.txt",b)

for i in range(16):
    plt.plot(b[i],alpha=0.8)
    plt.xlabel("VPED in mV")
    plt.ylabel("DAC counts")
    plt.title("VPED Transfer Functions")
plt.savefig("plots/all_VPED_tfs.png")
plt.savefig("plots/all_VPED_tfs.pdf")
