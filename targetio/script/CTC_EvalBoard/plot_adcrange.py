import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('TkAgg')

adc=[391,397,464,548,663,974,2143,3202,3589] #isel = 2550
#adc=[267,270,310,368,446,649,1422,2122,2380] #isel =2450
mV=[300,400,600,700,800,1000,1500,2000,2200]

adctc=[606,2033,3212,3652]
mVtc=[800,1500,2000,2200]

xvals=np.arange(0,2500)

f=interpolate.interp1d(mV,adc,fill_value="extrapolate")
yvals=f(xvals)
plt.title("CTC @104MCounts/s, TC @500MCounts/s")
plt.plot(xvals,yvals,label="extra/interpolate",color="tab:blue",alpha=0.5)
plt.plot(mV,adc,linestyle="",marker="o",label="CTC measured",color="tab:blue")
plt.plot(mVtc,adctc,linestyle="",marker="o",label="TC measured",color="tab:orange")
plt.legend()
plt.grid()
plt.xlabel("DC level in mV")
plt.ylabel("ADC counts")
plt.ylim(0,4095)
plt.show()
