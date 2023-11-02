import matplotlib.pyplot as plt
import numpy as np

data0=np.loadtxt('data/VPED_TF_0.txt')
data1=np.loadtxt('data/VPED_TF_1.txt')
data4=np.loadtxt('data/VPED_TF_4.txt')
data13=np.loadtxt('data/VPED_TF_13.txt')
data14=np.loadtxt('data/VPED_TF_14.txt')
data15=np.loadtxt('data/VPED_TF_15.txt')

vpeds0=data0[:,0]
volts0=data0[:,1]

vpeds1=data1[:,0]
volts1=data1[:,1]

vpeds4=data4[:,0]
volts4=data4[:,1]

vpeds13=data13[:,0]
volts13=data13[:,1]

vpeds14=data14[:,0]
volts14=data14[:,1]

vpeds15=data15[:,0]
volts15=data15[:,1]


grad0=np.zeros(len(vpeds0))
grad1=np.zeros(len(vpeds0))
grad4=np.zeros(len(vpeds0))
grad13=np.zeros(len(vpeds0))
grad14=np.zeros(len(vpeds0))
grad15=np.zeros(len(vpeds0))
for i in range(1,len(vpeds0)):
    grad0[i]=(volts0[i]-volts0[i-1])/(vpeds0[i]-vpeds0[i-1])
    grad1[i]=(volts1[i]-volts1[i-1])/(vpeds0[i]-vpeds0[i-1])
    grad4[i]=(volts4[i]-volts4[i-1])/(vpeds0[i]-vpeds0[i-1])
    grad13[i]=(volts13[i]-volts13[i-1])/(vpeds0[i]-vpeds0[i-1])
    grad14[i]=(volts14[i]-volts14[i-1])/(vpeds0[i]-vpeds0[i-1])
    grad15[i]=(volts15[i]-volts15[i-1])/(vpeds0[i]-vpeds0[i-1])


volts_mean=(volts0+volts1+volts4+volts13+volts14+volts15)/6
gradient=(volts_mean[400]-volts_mean[100])/(vpeds0[400]-vpeds0[100])
offset=volts_mean[100]-vpeds0[100]*gradient
volts_lin=(vpeds0*gradient)+offset



print("Gradient:",gradient,"Offset:",offset)

plt.plot(volts0,alpha=0.3,label="Channel 0")
plt.plot(volts_lin,alpha=0.3,label="Linear")

plt.show()

plt.plot(vpeds0,np.zeros(512),color="grey")
plt.plot(vpeds0,(grad0),alpha=0.3,label="Channel 0",marker='o')
plt.plot(vpeds0,(grad1),alpha=0.3,label="Channel 1")
plt.plot(vpeds0,(grad4),alpha=0.3,label="Channel 4")
plt.plot(vpeds0,(grad13),alpha=0.3,label="Channel 13")
plt.plot(vpeds0,(grad14),alpha=0.3,label="Channel 14")
plt.plot(vpeds0,(grad15),alpha=0.3,label="Channel 15")

plt.legend()
plt.ylabel("DNL in mV")
plt.xlabel("VPED in DAC counts")
plt.savefig("plots/dnl.pdf")
plt.savefig("plots/dnl.png")
plt.show()


plt.plot(vpeds0,np.zeros(512),color="grey")
plt.plot(vpeds0,(volts0-volts_mean),alpha=0.3,label="Channel 0")
plt.plot(vpeds0,(volts1-volts_mean),alpha=0.3,label="Channel 1")
plt.plot(vpeds0,(volts4-volts_mean),alpha=0.3,label="Channel 4")
plt.plot(vpeds0,(volts13-volts_mean),alpha=0.3,label="Channel 13")
plt.plot(vpeds0,(volts14-volts_mean),alpha=0.3,label="Channel 14")
plt.plot(vpeds0,(volts15-volts_mean),alpha=0.3,label="Channel 15")


plt.legend()
plt.ylabel("Voltage - Mean in mV")
plt.xlabel("VPED in DAC counts")
plt.savefig("plots/voltage-mean.png")
plt.savefig("plots/voltage-mean.pdf")
plt.show()

plt.plot(vpeds0,np.zeros(512),color="grey")
plt.plot(vpeds0,(volts0-volts_lin),alpha=0.3,label="Channel 0")
plt.plot(vpeds0,(volts1-volts_lin),alpha=0.3,label="Channel 1")
plt.plot(vpeds0,(volts4-volts_lin),alpha=0.3,label="Channel 4")
plt.plot(vpeds0,(volts13-volts_lin),alpha=0.3,label="Channel 13")
plt.plot(vpeds0,(volts14-volts_lin),alpha=0.3,label="Channel 14")
plt.plot(vpeds0,(volts15-volts_lin),alpha=0.3,label="Channel 15")

plt.legend()
plt.ylabel("INL in mV")
plt.xlabel("VPED in DAC counts")
plt.savefig("plots/inl.pdf")
plt.savefig("plots/inl.png")
plt.show()
